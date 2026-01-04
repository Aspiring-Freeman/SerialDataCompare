# -*- coding: utf-8 -*-
"""
分析历史记录管理 - SQLite版本
提供比JSON更可靠的历史记录存储
"""
import sqlite3
import json
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager


class AnalysisHistoryDB:
    """分析历史记录管理器（SQLite版本）"""
    
    # 数据库版本，用于未来升级迁移
    DB_VERSION = 1
    
    def __init__(self, max_history: int = 100):
        """
        初始化
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self.db_dir = Path.home() / '.serialdatacompare'
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / 'analysis_history.db'
        
        # 线程锁，确保并发安全
        self._lock = threading.RLock()
        
        # 初始化数据库
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建元数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                
                # 检查数据库版本
                cursor.execute('SELECT value FROM metadata WHERE key = ?', ('db_version',))
                row = cursor.fetchone()
                current_version = int(row['value']) if row else 0
                
                if current_version < self.DB_VERSION:
                    self._migrate_db(cursor, current_version)
                    cursor.execute('''
                        INSERT OR REPLACE INTO metadata (key, value)
                        VALUES ('db_version', ?)
                    ''', (str(self.DB_VERSION),))
                
                # 创建分析历史记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        protocol_name TEXT NOT NULL,
                        input_data TEXT,
                        total_frames INTEGER DEFAULT 0,
                        valid_frames INTEGER DEFAULT 0,
                        error_frames INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT (datetime('now', 'localtime'))
                    )
                ''')
                
                # 创建帧详情表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS frame_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        history_id INTEGER NOT NULL,
                        frame_number INTEGER NOT NULL,
                        has_error INTEGER DEFAULT 0,
                        checksum_valid INTEGER DEFAULT 1,
                        raw_data_hex TEXT,
                        fields_json TEXT,
                        FOREIGN KEY (history_id) REFERENCES analysis_history (id)
                            ON DELETE CASCADE
                    )
                ''')
                
                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_history_timestamp 
                    ON analysis_history (timestamp DESC)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_frame_history 
                    ON frame_details (history_id)
                ''')
    
    def _migrate_db(self, cursor, from_version: int):
        """数据库迁移"""
        # 预留迁移逻辑
        if from_version == 0:
            # 首次创建，无需迁移
            pass
        # 未来版本升级时在这里添加迁移逻辑
    
    def add_analysis(self, protocol_name: str, input_data: str, 
                    total_frames: int, valid_frames: int, error_frames: int,
                    frame_details: List[Dict[str, Any]]) -> int:
        """
        添加分析记录
        
        Args:
            protocol_name: 协议名称
            input_data: 输入数据
            total_frames: 总帧数
            valid_frames: 有效帧数
            error_frames: 错误帧数
            frame_details: 帧详情列表
            
        Returns:
            新记录的ID
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 插入主记录
                timestamp = datetime.now().isoformat()
                # 截断长数据
                truncated_data = input_data[:500] + '...' if len(input_data) > 500 else input_data
                
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (timestamp, protocol_name, input_data, total_frames, valid_frames, error_frames)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, protocol_name, truncated_data, 
                      total_frames, valid_frames, error_frames))
                
                history_id = cursor.lastrowid
                
                # 插入帧详情（最多保存前20帧）
                for frame in frame_details[:20]:
                    fields_json = json.dumps(frame.get('fields', {}), ensure_ascii=False)
                    cursor.execute('''
                        INSERT INTO frame_details 
                        (history_id, frame_number, has_error, checksum_valid, raw_data_hex, fields_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (history_id, 
                          frame.get('frame_number', 0),
                          1 if frame.get('has_error') else 0,
                          1 if frame.get('checksum_valid', True) else 0,
                          frame.get('raw_data_hex', ''),
                          fields_json))
                
                # 清理旧记录
                self._cleanup_old_records(cursor)
                
                return history_id
    
    def _cleanup_old_records(self, cursor):
        """清理超出限制的旧记录"""
        cursor.execute('''
            DELETE FROM analysis_history
            WHERE id NOT IN (
                SELECT id FROM analysis_history
                ORDER BY timestamp DESC
                LIMIT ?
            )
        ''', (self.max_history,))
    
    def get_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取历史记录列表
        
        Args:
            limit: 限制返回记录数，None表示使用默认限制
            
        Returns:
            历史记录列表
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                limit = limit or self.max_history
                cursor.execute('''
                    SELECT * FROM analysis_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                records = []
                for row in cursor.fetchall():
                    record = dict(row)
                    # 获取帧摘要
                    cursor.execute('''
                        SELECT frame_number, has_error, checksum_valid, raw_data_hex
                        FROM frame_details
                        WHERE history_id = ?
                        ORDER BY frame_number
                        LIMIT 10
                    ''', (record['id'],))
                    
                    record['frame_summary'] = [
                        {
                            'frame_number': f['frame_number'],
                            'has_error': bool(f['has_error']),
                            'checksum_valid': bool(f['checksum_valid']),
                            'raw_data_hex': f['raw_data_hex']
                        }
                        for f in cursor.fetchall()
                    ]
                    records.append(record)
                
                return records
    
    def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        获取指定ID的记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            记录详情，不存在返回None
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM analysis_history WHERE id = ?
                ''', (record_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                record = dict(row)
                
                # 获取完整帧详情
                cursor.execute('''
                    SELECT * FROM frame_details
                    WHERE history_id = ?
                    ORDER BY frame_number
                ''', (record_id,))
                
                record['frame_details'] = [
                    {
                        'frame_number': f['frame_number'],
                        'has_error': bool(f['has_error']),
                        'checksum_valid': bool(f['checksum_valid']),
                        'raw_data_hex': f['raw_data_hex'],
                        'fields': json.loads(f['fields_json']) if f['fields_json'] else {}
                    }
                    for f in cursor.fetchall()
                ]
                
                return record
    
    def get_record_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        按索引获取记录（兼容旧API）
        
        Args:
            index: 索引（0为最新）
            
        Returns:
            记录详情
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id FROM analysis_history
                    ORDER BY timestamp DESC
                    LIMIT 1 OFFSET ?
                ''', (index,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self.get_record(row['id'])
    
    def clear_history(self):
        """清空所有历史记录"""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM frame_details')
                cursor.execute('DELETE FROM analysis_history')
    
    def delete_record(self, record_id: int) -> bool:
        """
        删除指定记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否删除成功
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM analysis_history WHERE id = ?', (record_id,))
                return cursor.rowcount > 0
    
    def search_history(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索历史记录
        
        Args:
            keyword: 搜索关键词
            limit: 限制返回数量
            
        Returns:
            匹配的记录列表
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                search_pattern = f'%{keyword}%'
                cursor.execute('''
                    SELECT * FROM analysis_history
                    WHERE protocol_name LIKE ? OR input_data LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (search_pattern, search_pattern, limit))
                
                return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute('SELECT COUNT(*) FROM analysis_history')
                total_count = cursor.fetchone()[0]
                
                # 按协议统计
                cursor.execute('''
                    SELECT protocol_name, COUNT(*) as count
                    FROM analysis_history
                    GROUP BY protocol_name
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                protocols = {row['protocol_name']: row['count'] for row in cursor.fetchall()}
                
                # 帧统计
                cursor.execute('''
                    SELECT 
                        SUM(total_frames) as total,
                        SUM(valid_frames) as valid,
                        SUM(error_frames) as error
                    FROM analysis_history
                ''')
                frame_stats = dict(cursor.fetchone())
                
                return {
                    'total_records': total_count,
                    'protocols': protocols,
                    'total_frames': frame_stats['total'] or 0,
                    'valid_frames': frame_stats['valid'] or 0,
                    'error_frames': frame_stats['error'] or 0
                }
    
    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """格式化时间戳"""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    def migrate_from_json(self, json_path: str) -> int:
        """
        从旧的JSON格式迁移数据
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            迁移的记录数
        """
        if not os.path.exists(json_path):
            return 0
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if not isinstance(json_data, list):
                return 0
            
            count = 0
            for record in json_data:
                self.add_analysis(
                    protocol_name=record.get('protocol_name', '未知'),
                    input_data=record.get('input_data', ''),
                    total_frames=record.get('total_frames', 0),
                    valid_frames=record.get('valid_frames', 0),
                    error_frames=record.get('error_frames', 0),
                    frame_details=record.get('frame_summary', [])
                )
                count += 1
            
            return count
        except Exception as e:
            print(f"迁移JSON数据失败: {e}")
            return 0
