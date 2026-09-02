#!/usr/bin/env python3
"""
Migration script: Add Google login fields to existing users.

Backfills auth_provider="local" for users missing it.
Creates sparse unique index on google_id.
Supports --dry-run to preview changes without writing.

Usage:
    python3 scripts/migrate_add_google_fields.py
    python3 scripts/migrate_add_google_fields.py --dry-run
"""
import argparse
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


async def main(dry_run: bool = False) -> None:
    """Run the migration."""
    client = None
    try:
        client = AsyncIOMotorClient(settings.database_url)
        db = client[settings.database_url.split('/')[-1].split('?')[0]]
        collection = db['users']

        print("=" * 60)
        print(f"Google Login Migration {'(DRY RUN)' if dry_run else ''}")
        print("=" * 60)

        # Step 1: Backfill auth_provider for existing users
        backfill_filter = {'auth_provider': {'$exists': False}}
        backfill_count = await collection.count_documents(backfill_filter)

        if dry_run:
            print(f"\n[DRY RUN] Would backfill auth_provider='local' for {backfill_count} documents")
        else:
            if backfill_count > 0:
                result = await collection.update_many(
                    backfill_filter,
                    {'$set': {'auth_provider': 'local'}},
                )
                print(f"\nBackfilled auth_provider='local' for {result.modified_count} documents")
            else:
                print("\nNo documents need auth_provider backfill")

        # Step 2: Create sparse unique index on google_id
        index_name = 'google_id_1'
        index_spec = [('google_id', 1)]

        if dry_run:
            print(f"\n[DRY RUN] Would create sparse unique index: {index_name}")
            print(f"  Index spec: {index_spec}, unique=True, sparse=True")
        else:
            try:
                await collection.create_index(
                    index_spec,
                    unique=True,
                    sparse=True,
                    name=index_name,
                )
                print(f"\nCreated sparse unique index: {index_name}")
            except Exception as exc:
                print(f"\nIndex creation note: {exc}")

        # Summary
        total_users = await collection.count_documents({})
        google_users = await collection.count_documents({'google_id': {'$exists': True, '$ne': None}})

        print(f"\n{'=' * 60}")
        print(f"Summary:")
        print(f"  Total users: {total_users}")
        print(f"  Users with google_id: {google_users}")
        print(f"  Auth provider backfill: {backfill_count} ({'would be ' if dry_run else ''}modified)")
        print(f"{'=' * 60}")

    except Exception as exc:
        print(f"Migration error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        if client:
            client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add Google login fields to existing users')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
