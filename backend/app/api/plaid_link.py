"""
API для Plaid Link - получение новых токенов
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/plaid", tags=["plaid-link"])

def get_plaid_client():
    """Получаем Plaid клиент"""
    import plaid
    from plaid.api import plaid_api
    from plaid import Configuration, ApiClient, Environment
    
    client_id = os.getenv("PLAID_CLIENT_ID")
    secret = os.getenv("PLAID_SECRET")
    environment = os.getenv("PLAID_ENVIRONMENT", "production")
    
    if not client_id or not secret:
        raise HTTPException(status_code=500, detail="Plaid credentials not configured")
    
    configuration = Configuration(
        host=Environment.Production if environment == 'production' else Environment.Sandbox,
        api_key={
            'clientId': client_id,
            'secret': secret
        }
    )
    api_client = ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)

class PlaidLinkConfig(BaseModel):
    client_id: str
    environment: str
    products: list
    country_codes: list
    language: str = "en"

class PlaidLinkTokenRequest(BaseModel):
    public_token: str
    institution_id: str
    institution_name: str

class PlaidLinkTokenResponse(BaseModel):
    access_token: str
    item_id: str
    institution_id: str
    institution_name: str

@router.get("/link/config")
async def get_plaid_link_config():
    """Получаем конфигурацию для Plaid Link"""
    try:
        # Создаем link_token для Plaid Link v2
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.country_code import CountryCode
        from plaid.model.products import Products
        
        plaid_client = get_plaid_client()
        
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Budget Manager Cloud",
            country_codes=[CountryCode('CA'), CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='user-1')
        )
        response = plaid_client.link_token_create(request)
        
        return {
            "link_token": response['link_token'],
            "environment": os.getenv("PLAID_ENVIRONMENT", "production")
        }
    except Exception as e:
        print(f"Ошибка создания link_token: {e}")
        # Fallback на старую конфигурацию
        return {
            "client_id": os.getenv("PLAID_CLIENT_ID"),
            "environment": os.getenv("PLAID_ENVIRONMENT", "production"),
            "products": ["transactions"],
            "country_codes": ["CA", "US"],
            "language": "en",
        }

@router.post("/link/exchange")
async def exchange_public_token(request: PlaidLinkTokenRequest):
    """Обмениваем public token на access token"""
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
        from plaid import Configuration, ApiClient
        
        # Настройка Plaid клиента
        configuration = Configuration(
            host=plaid.Environment.Production if os.getenv("PLAID_ENVIRONMENT") == "production" else plaid.Environment.Sandbox,
            api_key={
                'clientId': os.getenv("PLAID_CLIENT_ID"),
                'secret': os.getenv("PLAID_SECRET")
            }
        )
        
        api_client = ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)
        
        # Обмен public token на access token
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=request.public_token
        )
        
        response = client.item_public_token_exchange(exchange_request)
        
        # Save bank to BankManager and database
        from ..api.bank_management import bank_manager

        await bank_manager.add_bank(
            name=request.institution_name,
            access_token=response['access_token'],
            plaid_institution_id=request.institution_id,
            item_id=response['item_id']
        )
        
        print(f"Bank {request.institution_name} ({request.institution_id}) successfully added to BankManager and DB")
        
        return PlaidLinkTokenResponse(
            access_token=response['access_token'],
            item_id=response['item_id'],
            institution_id=request.institution_id,
            institution_name=request.institution_name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обмена токена: {str(e)}")

@router.get("/institutions")
async def get_supported_institutions():
    """Получаем список поддерживаемых банков"""
    return {
        "institutions": [
            {
                "id": "rbc",
                "name": "Royal Bank of Canada",
                "country": "CA",
                "products": ["transactions"],
                "logo": "https://cdn.plaid.com/institution_logos/rbc.png"
            },
            {
                "id": "bmo",
                "name": "Bank of Montreal",
                "country": "CA", 
                "products": ["transactions"],
                "logo": "https://cdn.plaid.com/institution_logos/bmo.png"
            },
            {
                "id": "cibc",
                "name": "Canadian Imperial Bank of Commerce",
                "country": "CA",
                "products": ["transactions"],
                "logo": "https://cdn.plaid.com/institution_logos/cibc.png"
            },
            {
                "id": "walmart",
                "name": "Walmart Rewards",
                "country": "CA",
                "products": ["transactions"],
                "logo": "https://cdn.plaid.com/institution_logos/walmart.png"
            }
        ]
    }

@router.post("/link/update")
async def update_existing_item(request: PlaidLinkTokenRequest):
    """Обновляем существующий item через Plaid Link в update mode"""
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
        from plaid import Configuration, ApiClient
        
        # Настройка Plaid клиента
        configuration = Configuration(
            host=plaid.Environment.Production if os.getenv("PLAID_ENVIRONMENT") == "production" else plaid.Environment.Sandbox,
            api_key={
                'clientId': os.getenv("PLAID_CLIENT_ID"),
                'secret': os.getenv("PLAID_SECRET")
            }
        )
        api_client = ApiClient(configuration)
        plaid_client = plaid_api.PlaidApi(api_client)
        
        # Обмениваем public token на access token
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=request.public_token
        )
        plaid_client = get_plaid_client()
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        
        # Обновляем .env файл
        bank_code = request.institution_id.upper()
        
        # Читаем текущий .env
        env_path = os.path.join(os.getcwd(), '.env')
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
        
        # Обновляем токены
        new_env_content = []
        for line in env_content.splitlines():
            if f"{bank_code}_ACCESS_TOKEN=" in line:
                new_env_content.append(f"{bank_code}_ACCESS_TOKEN={access_token}")
            elif f"{bank_code}_ITEM_ID=" in line:
                new_env_content.append(f"{bank_code}_ITEM_ID={item_id}")
            else:
                new_env_content.append(line)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_env_content))
        
        return {"access_token": access_token, "item_id": item_id, "message": "Item updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления item: {e}")
