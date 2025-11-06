# primeira coisa
from fastapi import APIRouter

router = APIRouter(prefix='/membros', tags=['membros'])


@router.get('/')
def read_membros():
    return 'opa'
