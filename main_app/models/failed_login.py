from app_init import mysql
import datetime
from models.user import User

class FailedLogin:

    @classmethod
    def verify_log_in(clazz, ip_address:str, user:str):
        if len(ip_address) > 30:
            ip_address = ip_address[0:30]

        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            cursor.execute("""
                SELECT created_at FROM failed_logins
                WHERE created_at > NOW() - INTERVAL 10 MINUTE
            """)

            last_10_minutes = cursor.rowcount

            if last_10_minutes >= 7:
                return False, "Zbyt dużo prób logowania. Odczekaj chwilę przed następną próbą"

            rows = cursor.fetchall()
            last_3_minutes = 0
            last_3_minute_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=3)

            for row in rows:
                if row["created_at"] > last_3_minute_time:
                    last_3_minutes += 1

            if last_3_minutes >= 3:
                return False, "Zbyt dużo prób logowania. Odczekaj chwilę przed następną próbą"

            cursor.execute("""
                SELECT fl.created_at 
                FROM failed_logins fl
                JOIN user u ON u.id = fl.user_id
                WHERE u.login=%(login)s AND fl.created_at > NOW() - INTERVAL 10 MINUTE
            """, {
                "login": user
            })
            if cursor.rowcount > 10:
                return False, "Konto zostało tymczasowo zablokowane"

            return True, None

    @classmethod
    def register_failed_attempt(clazz, ip_address:str, user:User):
        if len(ip_address) > 30:
            ip_address = ip_address[0:30]

        mysql.prepare_connection()
        with mysql.cursor() as cursor:
            if user is not None:
                cursor.execute("""
                    INSERT INTO failed_logins (ip_address, user_id) VALUES (%(ip_address)s, %(user_id)s)
                """, {
                    "ip_address": ip_address,
                    "user_id": user.id
                })
            else:
                cursor.execute("""
                    INSERT INTO failed_logins (ip_address, user_id) VALUES (%(ip_address)s, NULL)
                """, {
                    "ip_address": ip_address
                })
            mysql.commit()