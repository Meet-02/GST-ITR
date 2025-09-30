# In calc_bus.py

def calc_bus_tax_new_regime(gross_revenue, total_business_expenses):
    # 1. Calculate business profit
    taxable_income = gross_revenue - total_business_expenses
    if taxable_income < 0:
        taxable_income = 0

    tax = 0
    # 2. Apply tax slabs
    if taxable_income > 1500000:
        tax = (taxable_income - 1500000) * 0.30 + 150000
    elif taxable_income > 1200000:
        tax = (taxable_income - 1200000) * 0.20 + 90000
    elif taxable_income > 900000:
        tax = (taxable_income - 900000) * 0.15 + 45000
    elif taxable_income > 600000:
        tax = (taxable_income - 600000) * 0.10 + 15000
    elif taxable_income > 300000:
        tax = (taxable_income - 300000) * 0.05
    
    # 3. Add Cess
    cess = tax * 0.04
    total_tax_liability = tax + cess
    
    return total_tax_liability, taxable_income