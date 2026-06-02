from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import text

class WordpressUserRepository:

    def __init__(self, db: Session):
        self.db = db

    def searchUsers(self, search: str) -> List[dict]:
        searchValue = f"%{search.strip()}%"

        query = text("""
            SELECT
                ID AS wordpressUserId,
                user_login AS wordpressUserLogin,
                user_email AS wordpressUserEmail,
                display_name AS wordpressDisplayName
            FROM wp_users
            WHERE
                user_login LIKE :search
                OR user_email LIKE :search
                OR display_name LIKE :search
            ORDER BY display_name ASC
            LIMIT 20
        """)

        result = self.db.execute(query, {"search": searchValue})
        return [dict(row._mapping) for row in result]

    def getById(self, wordpressUserId: int) -> Optional[dict]:
        query = text("""
            SELECT
                ID AS wordpressUserId,
                user_login AS wordpressUserLogin,
                user_email AS wordpressUserEmail,
                display_name AS wordpressDisplayName,
                user_pass AS wordpressUserPass
            FROM wp_users
            WHERE ID = :wordpressUserId
            LIMIT 1
        """)

        result = self.db.execute(query, {"wordpressUserId": wordpressUserId}).first()

        if not result:
            return None

        return dict(result._mapping)

    def getByLoginOrEmail(self, username: str) -> Optional[dict]:
        query = text("""
            SELECT
                ID AS wordpressUserId,
                user_login AS wordpressUserLogin,
                user_email AS wordpressUserEmail,
                display_name AS wordpressDisplayName,
                user_pass AS wordpressUserPass
            FROM wp_users
            WHERE user_login = :username OR user_email = :username
            LIMIT 1
        """)

        result = self.db.execute(query, {"username": username.strip()}).first()

        if not result:
            return None

        return dict(result._mapping)

    def getByLogin(self, userLogin: str) -> Optional[dict]:
        query = text("""
            SELECT
                ID AS wordpressUserId,
                user_login AS wordpressUserLogin,
                user_email AS wordpressUserEmail,
                display_name AS wordpressDisplayName,
                user_pass AS wordpressUserPass
            FROM wp_users
            WHERE user_login = :userLogin
            LIMIT 1
        """)

        result = self.db.execute(query, {"userLogin": userLogin.strip()}).first()

        if not result:
            return None

        return dict(result._mapping)