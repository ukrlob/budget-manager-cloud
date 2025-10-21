"""
Service for managing banks in the database
"""

import logging
from typing import List, Optional

from ..models.bank import Bank, BankCreate
from ..models.database import db

logger = logging.getLogger(__name__)


class BankService:
    """Service for bank-related database operations"""

    async def get_all_banks(self) -> List[Bank]:
        """Get all banks from the database"""
        query = "SELECT id, name, country, currency, access_token, item_id, plaid_institution_id, created_at FROM banks"
        try:
            banks_data = await db.execute_query(query)
            if not banks_data:
                return []
            return [Bank(**bank) for bank in banks_data]
        except Exception as e:
            logger.error(f"Error getting all banks: {e}")
            return []

    async def create_bank(self, bank: BankCreate) -> Optional[Bank]:
        """Create a new bank or update it if it already exists"""
        query = """
            INSERT INTO banks (name, country, currency, access_token, item_id, plaid_institution_id)
            VALUES (%(name)s, %(country)s, %(currency)s, %(access_token)s, %(item_id)s, %(plaid_institution_id)s)
            ON CONFLICT (plaid_institution_id) DO UPDATE SET
                name = EXCLUDED.name,
                country = EXCLUDED.country,
                currency = EXCLUDED.currency,
                access_token = EXCLUDED.access_token,
                item_id = EXCLUDED.item_id,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, name, country, currency, access_token, item_id, plaid_institution_id, created_at
        """
        try:
            # The execute_query method is more suitable here as it can return the inserted row.
            created_bank_data_list = await db.execute_query(query, bank.model_dump())
            if created_bank_data_list:
                return Bank(**created_bank_data_list[0])
            return None
        except Exception as e:
            logger.error(f"Error creating/updating bank {bank.name}: {e}")
            return None

    async def get_bank_by_plaid_institution_id(self, plaid_institution_id: str) -> Optional[Bank]:
        """Get a bank by its Plaid institution ID"""
        query = "SELECT id, name, country, currency, access_token, item_id, plaid_institution_id, created_at FROM banks WHERE plaid_institution_id = %(plaid_institution_id)s"
        try:
            bank_data_list = await db.execute_query(query, {"plaid_institution_id": plaid_institution_id})
            if bank_data_list:
                return Bank(**bank_data_list[0])
            return None
        except Exception as e:
            logger.error(f"Error getting bank by plaid_institution_id {plaid_institution_id}: {e}")
            return None
