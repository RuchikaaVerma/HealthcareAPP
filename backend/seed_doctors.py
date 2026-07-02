"""
Seed script to populate the database with 30 realistic doctors of different specialties.
Run with: python -m seed_doctors
"""
import sys
import os
from datetime import time

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.doctor import Doctor, WorkingHours

SPECIALTIES = [
    ("Cardiology", "Specialist in heart and cardiovascular health, offering advanced diagnostics, lifestyle plans, and treatment for chronic cardiac conditions."),
    ("Pediatrics", "Dedicated pediatric care covering childhood development, immunisations, and treatment of acute or chronic pediatric illnesses."),
    ("Neurosurgeon", "Board-certified neurosurgeon specialising in minimally invasive spinal surgeries, brain tumor removals, and nerve disorders."),
    ("Dermatology", "Expert in skin health, addressing acne, eczema, psoriasis, skin cancer checks, and medical aesthetic treatments."),
    ("General Physician", "Comprehensive family healthcare focusing on preventive medicine, chronic disease management, and wellness checks."),
    ("Gynecology", "Empathetic women's reproductive health, prenatal care, fertility consultations, and menopause management."),
    ("Orthopedics", "Specialist in joint replacements, sports injuries, fracture management, and muscular health."),
    ("Psychiatry", "Providing mental health support, psychiatric evaluations, counseling, and medical management of psychological wellness."),
    ("Ophthalmology", "Comprehensive eye examinations, treatment of cataracts, glaucoma, macular degeneration, and vision care."),
    ("Endocrinology", "Expertise in diabetes management, thyroid disorders, hormonal imbalances, and metabolism health."),
    ("Gastroenterology", "Specialising in digestive health, acid reflux management, IBS treatment, and diagnostic endoscopies."),
    ("Oncology", "Compassionate cancer care offering state-of-the-art chemotherapies, immunotherapy plans, and solid tumor management."),
    ("Nephrology", "Specialised care for kidney health, hypertension management, and dialysis counseling."),
    ("Urology", "Urological healthcare focusing on prostate health, urinary tract infections, and kidney stone management."),
    ("Pulmonology", "Treating respiratory health, asthma, COPD, chronic cough, and sleep apnea conditions."),
    ("Rheumatology", "Expert diagnosis and care for autoimmune diseases, rheumatoid arthritis, lupus, and joint pain."),
    ("ENT (Otolaryngology)", "Treating sinus infections, hearing loss, tonsil conditions, and allergy-related throat problems."),
    ("Neurology", "Non-surgical brain and nervous system specialist handling migraines, epilepsy, and neuropathy."),
    ("Geriatrics", "Compassionate age-focused medical care for elderly patients, managing polypharmacy and cognitive health."),
    ("Allergy & Immunology", "Diagnostics and treatment for seasonal allergies, asthma triggers, and immune deficiencies."),
    ("Hematology", "Managing blood disorders, anemia, clotting issues, and blood-related wellness."),
    ("Infectious Disease", "Specialised care for complex bacterial, viral, or tropical infections."),
    ("Sports Medicine", "Non-surgical sports injury recovery, physical fitness guidance, and performance improvement."),
    ("Podiatry", "Specialist in foot and ankle health, diabetic foot care, and orthotics design."),
    ("Plastic Surgery", "Reconstructive surgeries, wound healing, and advanced cosmetic surgery consultations."),
    ("Vascular Surgery", "Managing circulatory system disorders, varicose veins, and arterial health."),
    ("Medical Genetics", "Genetic testing, hereditary risk assessments, and rare disorder counseling."),
    ("Family Medicine", "Continuity of care for all ages, focusing on long-term family medical histories and habits."),
    ("Hepatology", "Liver specialist dealing with hepatitis, fatty liver disease, and cirrhosis management."),
    ("Sleep Medicine", "Diagnosing and treating insomnia, sleep apnea, restless leg syndrome, and circadian rhythm disorders.")
]

DOCTOR_NAMES = [
    "Dr. Amit Sharma", "Dr. Sarah Jenkins", "Dr. Priya Patel", "Dr. Marcus Vance", "Dr. Rajesh Iyer",
    "Dr. Emily Watson", "Dr. Vikram Seth", "Dr. Chloe Dubois", "Dr. Rohan Verma", "Dr. Aisha Khan",
    "Dr. David Miller", "Dr. Sneha Rao", "Dr. Liam O'Connor", "Dr. Neha Gupta", "Dr. Carlos Santos",
    "Dr. Ananya Das", "Dr. Kenji Tanaka", "Dr. Sofia Rossi", "Dr. Kabir Malhotra", "Dr. Elena Petrova",
    "Dr. Sanjay Dutt", "Dr. Olivia Bennett", "Dr. Devendra Singh", "Dr. Isabella Silva", "Dr. Arjun Kapoor",
    "Dr. Min-Jae Kim", "Dr. Clara Fischer", "Dr. Nikhil Nair", "Dr. Grace Hopper", "Dr. Vikram Aditya"
]

def seed():
    db = SessionLocal()
    try:
        # Delete any doctor users who don't have a doctor profile (orphans from aborted runs)
        orphan_users = db.query(User).filter(User.role == UserRole.DOCTOR).all()
        deleted_count = 0
        for u in orphan_users:
            doc = db.query(Doctor).filter(Doctor.user_id == u.id).first()
            if not doc:
                db.delete(u)
                deleted_count += 1
        if deleted_count > 0:
            db.commit()
            print(f"Cleaned up {deleted_count} orphan doctor users.")

        # Avoid seeding if we already have 30 doctors to prevent duplication
        existing_doc_count = db.query(Doctor).count()
        if existing_doc_count >= 30:
            print(f"Database already has {existing_doc_count} doctors. Seeding skipped.")
            return

        print(f"Beginning seeding of {len(SPECIALTIES)} doctors...")
        pwd_hash = hash_password("DoctorPassword123!")

        for idx, (spec, bio) in enumerate(SPECIALTIES):
            name = DOCTOR_NAMES[idx]
            # Strip "Dr. " prefix to avoid "dr.dr" email duplication
            clean_name = name.replace("Dr. ", "").strip()
            email = f"dr.{clean_name.lower().replace(' ', '.')}.vitalis@clinic.com"

            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"User {email} already exists, checking doctor profile...")
                doctor = db.query(Doctor).filter(Doctor.user_id == existing_user.id).first()
                if doctor:
                    continue
                user = existing_user
            else:
                user = User(
                    email=email,
                    hashed_password=pwd_hash,
                    full_name=name,
                    phone=f"+91 99887766{idx:02d}",
                    role=UserRole.DOCTOR
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            doctor = Doctor(
                user_id=user.id,
                specialisation=spec,
                bio=bio,
                slot_duration_minutes=30
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

            # Assign working hours (Mon-Fri, 9:00 to 17:00)
            for day in range(5):  # 0=Monday to 4=Friday
                wh = WorkingHours(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(17, 0)
                )
                db.add(wh)

            db.commit()
            print(f"Successfully seeded: {name} ({spec})")

        print("All doctors seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed due to error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
