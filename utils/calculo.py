def calcular_custo_total(custos: dict) -> float:
    return sum(custos.values())

def calcular_parcela(total: float, parcelas: int) -> float:
    return total / parcelas if parcelas > 0 else total
