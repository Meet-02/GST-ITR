def calculate_gst(purchase_value, purchase_gst_rate, purchase_supply_type, sell_value, sell_gst_rate, sell_supply_type):
    """
    Calculates the net GST payable based on purchase and sales data.
    """
    # --- 1. Calculate Input Tax (Tax Paid on Purchases) ---
    input_tax_total = purchase_value * (purchase_gst_rate / 100.0)
    input_cgst, input_sgst, input_igst = 0.0, 0.0, 0.0

    if purchase_supply_type == 'Intra-State':
        input_cgst = input_tax_total / 2
        input_sgst = input_tax_total / 2
    else: # Inter-State
        input_igst = input_tax_total

    # --- 2. Calculate Output Tax (Tax Collected on Sales) ---
    output_tax_total = sell_value * (sell_gst_rate / 100.0)
    output_cgst, output_sgst, output_igst = 0.0, 0.0, 0.0

    if sell_supply_type == 'Intra-State':
        output_cgst = output_tax_total / 2
        output_sgst = output_tax_total / 2
    else: # Inter-State
        output_igst = output_tax_total

    # --- 3. Calculate Net Tax Payable by setting off Input Tax Credit (ITC) ---
    
    # Start with the liabilities
    payable_cgst = output_cgst
    payable_sgst = output_sgst
    payable_igst = output_igst
    
    # Step A: Set off IGST credit
    # First, use IGST credit to pay IGST liability
    setoff = min(payable_igst, input_igst)
    payable_igst -= setoff
    input_igst -= setoff
    
    # Then, use remaining IGST credit to pay CGST liability
    setoff = min(payable_cgst, input_igst)
    payable_cgst -= setoff
    input_igst -= setoff
    
    # Then, use remaining IGST credit to pay SGST liability
    setoff = min(payable_sgst, input_igst)
    payable_sgst -= setoff
    input_igst -= setoff
    
    # Step B: Set off CGST credit
    # First, use CGST credit to pay CGST liability
    setoff = min(payable_cgst, input_cgst)
    payable_cgst -= setoff
    input_cgst -= setoff
    
    # Then, use remaining CGST credit to pay IGST liability
    setoff = min(payable_igst, input_cgst)
    payable_igst -= setoff
    input_cgst -= setoff
    
    # Step C: Set off SGST credit
    # First, use SGST credit to pay SGST liability
    setoff = min(payable_sgst, input_sgst)
    payable_sgst -= setoff
    input_sgst -= setoff
    
    # Then, use remaining SGST credit to pay IGST liability
    setoff = min(payable_igst, input_sgst)
    payable_igst -= setoff
    input_sgst -= setoff

    net_gst_payable = payable_cgst + payable_sgst + payable_igst

    results = {
        "input_tax": {
            "total": input_tax_total,
            # FIX: Use the original calculated values, not "input_cgst + setoff"
            "cgst": input_tax_total / 2 if purchase_supply_type == 'Intra-State' else 0,
            "sgst": input_tax_total / 2 if purchase_supply_type == 'Intra-State' else 0,
            "igst": input_tax_total if purchase_supply_type == 'Inter-State' else 0,
        },
        "output_tax": {
            # ... (this part was already correct) ...
            "total": output_tax_total,
            "cgst": output_cgst,
            "sgst": output_sgst,
            "igst": output_igst,
        },
        "net_payable": {
            # ... (this part was already correct) ...
            "total": net_gst_payable,
            "cgst": payable_cgst,
            "sgst": payable_sgst,
            "igst": payable_igst,
        }
    }
    return results