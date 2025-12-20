"""
SDE Ingestion Script

This script checks if the Fuzzwork SDE has been loaded into PostgreSQL.
If not, it executes pg_restore to load the dump file.

Usage:
    python -m app.scripts.ingest_sde
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from sqlalchemy import text
from app.database import engine


# Database configuration from environment
DB_USER = os.getenv("POSTGRES_USER", "eve_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "eve_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "eve_sde")

# SDE dump file location
SDE_DATA_DIR = Path(__file__).parent.parent.parent / "data"
SDE_DUMP_FILE = os.getenv("SDE_DUMP_FILE", "postgres-latest.dump")


async def check_sde_loaded() -> bool:
    """
    Check if SDE tables exist and are populated.
    Returns True if invTypes table exists and has data.
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'invTypes'"
                )
            )
            table_exists = result.scalar() > 0
            
            if not table_exists:
                print("❌ invTypes table does not exist")
                return False
            
            # Check if table has data
            result = await conn.execute(text("SELECT COUNT(*) FROM \"invTypes\""))
            row_count = result.scalar()
            
            if row_count > 0:
                print(f"✅ SDE already loaded - invTypes has {row_count:,} rows")
                return True
            else:
                print("⚠️  invTypes table exists but is empty")
                return False
                
    except Exception as e:
        print(f"⚠️  Error checking SDE status: {e}")
        return False


def find_dump_file() -> Path:
    """
    Find the SDE dump file in the data directory.
    """
    # Try exact filename from env
    exact_path = SDE_DATA_DIR / SDE_DUMP_FILE
    if exact_path.exists():
        return exact_path
    
    # Search for any .dump or .sql file
    for pattern in ["*.dump", "*.sql", "postgres-*.dump"]:
        matches = list(SDE_DATA_DIR.glob(pattern))
        if matches:
            return matches[0]
    
    raise FileNotFoundError(
        f"No SDE dump file found in {SDE_DATA_DIR}\n"
        f"Please download from https://www.fuzzwork.co.uk/dump/ "
        f"and place in backend/data/"
    )


def restore_sde_dump(dump_file: Path):
    """
    Restore the Fuzzwork SDE dump using pg_restore or psql.
    """
    print(f"📦 Restoring SDE from {dump_file.name}...")
    
    # Set PGPASSWORD environment variable
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    try:
        if dump_file.suffix == ".dump":
            # Use pg_restore for binary dumps
            cmd = [
                "pg_restore",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-v",  # Verbose
                "--no-owner",
                "--no-acl",
                str(dump_file)
            ]
        else:
            # Use psql for .sql files
            cmd = [
                "psql",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-f", str(dump_file)
            ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ SDE restore completed successfully")
            if result.stdout:
                print(result.stdout[-500:])  # Last 500 chars of output
        else:
            print(f"❌ SDE restore failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        print("❌ SDE restore timed out after 10 minutes")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ pg_restore/psql not found. Please install PostgreSQL client tools.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during restore: {e}")
        sys.exit(1)


async def validate_sde():
    """
    Validate that critical SDE tables are present and populated.
    """
    print("\n🔍 Validating SDE data...")
    
    critical_tables = [
        "invTypes",
        "mapSolarSystems",
        "mapSolarSystemJumps",
        "staStations",
        "invMarketGroups",
    ]
    
    async with engine.begin() as conn:
        for table in critical_tables:
            try:
                result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                
                if count > 0:
                    print(f"  ✅ {table}: {count:,} rows")
                else:
                    print(f"  ⚠️  {table}: 0 rows (might be expected)")
                    
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")


async def main():
    """
    Main ingestion workflow.
    """
    print("=" * 60)
    print("EVE Online SDE Ingestion Script")
    print("=" * 60)
    
    # Check if SDE is already loaded
    if await check_sde_loaded():
        print("\n✅ SDE already loaded. Skipping ingestion.")
        await validate_sde()
        return
    
    # Find dump file
    try:
        dump_file = find_dump_file()
        print(f"\n📁 Found dump file: {dump_file}")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    
    # Restore dump
    restore_sde_dump(dump_file)
    
    # Validate
    await validate_sde()
    
    print("\n" + "=" * 60)
    print("✅ SDE Ingestion Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
