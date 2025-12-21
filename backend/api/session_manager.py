"""
Session Manager for Evolution API

マルチユーザー対応のためのセッション管理を提供します。
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from neat_core.population_manager import PopulationManager


class SessionManager:
    """
    進化セッションを管理するクラス

    各ユーザーのPopulationManagerインスタンスをセッションIDで管理します。
    """

    def __init__(self, session_timeout_minutes: int = 60):
        """
        Args:
            session_timeout_minutes: セッションのタイムアウト時間（分）
        """
        self._sessions: Dict[str, PopulationManager] = {}
        self._last_access: Dict[str, datetime] = {}
        self._session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self, config_path: str, num_drones: int = 5) -> str:
        """
        新しいセッションを作成

        Args:
            config_path: NEAT設定ファイルパス
            num_drones: ドローン数

        Returns:
            str: 生成されたセッションID
        """
        session_id = str(uuid.uuid4())
        population_manager = PopulationManager(config_path, num_drones)

        self._sessions[session_id] = population_manager
        self._last_access[session_id] = datetime.now()

        return session_id

    def get_session(self, session_id: str) -> Optional[PopulationManager]:
        """
        セッションIDからPopulationManagerを取得

        Args:
            session_id: セッションID

        Returns:
            PopulationManager or None: セッションが存在する場合はPopulationManager
        """
        if session_id not in self._sessions:
            return None

        # 最終アクセス時刻を更新
        self._last_access[session_id] = datetime.now()
        return self._sessions[session_id]

    def delete_session(self, session_id: str) -> bool:
        """
        セッションを削除

        Args:
            session_id: セッションID

        Returns:
            bool: 削除に成功した場合True
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            del self._last_access[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        タイムアウトしたセッションを削除

        Returns:
            int: 削除されたセッション数
        """
        now = datetime.now()
        expired_sessions = [
            session_id
            for session_id, last_access in self._last_access.items()
            if now - last_access > self._session_timeout
        ]

        for session_id in expired_sessions:
            self.delete_session(session_id)

        return len(expired_sessions)

    def get_session_count(self) -> int:
        """
        アクティブなセッション数を取得

        Returns:
            int: セッション数
        """
        return len(self._sessions)

    def session_exists(self, session_id: str) -> bool:
        """
        セッションが存在するか確認

        Args:
            session_id: セッションID

        Returns:
            bool: セッションが存在する場合True
        """
        return session_id in self._sessions


# グローバルなSessionManagerインスタンス
# FastAPIのライフサイクルで管理
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    SessionManagerのシングルトンインスタンスを取得

    Returns:
        SessionManager: SessionManagerインスタンス
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
