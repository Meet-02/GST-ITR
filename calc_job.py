def calc_job_tax_new_regime(gross_income, tds):
    """
    Calculates tax for a salaried person under the NEW REGIME for FY 2024-25.
    """
    # 1. Apply the standard deduction for salaried individuals
    taxable_income = gross_income - 50000
    
    if taxable_income < 0:
        taxable_income = 0

    tax = 0
    # 2. Apply the correct tax slabs
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
    
    # 3. Health and Education Cess (4%)
    cess = tax * 0.04
    total_tax = tax + cess

    # 4. Subtract TDS from the final tax liability
    final_tax_due = total_tax - tds
    
    return final_tax_due, taxable_income