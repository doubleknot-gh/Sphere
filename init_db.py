from database import get_db
from models import Member, MemberStatus
from main import get_password_hash

def init_db_data():
    db = next(get_db())
    
    print("--- 데이터베이스 계정 초기화 시작 ---")

    # 1. 관리자 계정 (admin / admin1234)
    if not db.query(Member).filter(Member.student_id == "admin").first():
        admin_user = Member(
            student_id="admin",
            password=get_password_hash("admin1234"),
            name="총동연 관리자",
            club="총동아리연합회",
            status=MemberStatus.active,
            role="admin"
        )
        db.add(admin_user)
        print("✅ 관리자 계정 생성됨 (ID: admin)")
    else:
        print("ℹ️ 관리자 계정이 이미 존재합니다.")

    # 2. 테스트 계정 (20240001 / 1234)
    if not db.query(Member).filter(Member.student_id == "20240001").first():
        test_user = Member(
            student_id="20240001",
            password=get_password_hash("1234"),
            name="김테스트",
            club="테니스부",
            status=MemberStatus.active,
            role="member"
        )
        db.add(test_user)
        print("✅ 테스트 계정 생성됨 (ID: 20240001)")
    else:
        print("ℹ️ 테스트 계정이 이미 존재합니다.")

    db.commit()
    db.close()
    print("--- 초기화 완료 ---")

if __name__ == "__main__":
    init_db_data()