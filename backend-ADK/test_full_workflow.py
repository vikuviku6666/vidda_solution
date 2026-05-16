#!/usr/bin/env python3
"""Test the full workflow with a complete KYC Analyst description"""

import sys
import time

# Sample KYC Analyst role description
KYC_ROLE = """KYC Analyst responsible for customer due diligence, transaction monitoring, and risk assessment for high-risk clients in the financial services sector. This role conducts enhanced due diligence procedures, performs ongoing monitoring of customer relationships, identifies suspicious activities, and ensures compliance with AMLR 2024/1624 requirements. The analyst works closely with compliance teams to report potential money laundering risks and maintains detailed documentation of all KYC procedures."""

print("=" * 70)
print("FULL WORKFLOW TEST - KYC Analyst")
print("=" * 70)

try:
    from app.services.workflow import run_training_workflow
    
    print(f"\n📋 Input Role Description:")
    print(f"   {KYC_ROLE[:100]}...")
    print(f"\n🚀 Starting workflow...")
    print(f"   Expected time: 25-35 seconds")
    print(f"   Please wait...\n")
    
    start_time = time.time()
    
    # Run the workflow
    result = run_training_workflow(KYC_ROLE)
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ Workflow completed in {elapsed:.1f} seconds!")
    print("=" * 70)
    
    # Display results
    print(f"\n📊 RESULTS:")
    print(f"   Role: {result.role_data.role}")
    print(f"   Responsibilities: {len(result.role_data.responsibilities)}")
    print(f"   Risks identified: {len(result.risks)}")
    print(f"   Regulations: {len(result.regulations)}")
    print(f"   Recommendations (modules): {len(result.recommendations)}")
    print(f"   Training Plan ID: {result.training_plan_id}")
    
    print(f"\n📅 QUARTERLY TRAINING MODULES:")
    
    # Group by quarter
    quarters = {}
    for rec in result.recommendations:
        quarter = rec.quarter
        if quarter not in quarters:
            quarters[quarter] = []
        quarters[quarter].append(rec)
    
    for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
        if quarter in quarters:
            print(f"\n   {quarter}:")
            for module in quarters[quarter]:
                print(f"      • {module.module_name}")
                if hasattr(module, 'regulation_references') and module.regulation_references:
                    articles = ', '.join(module.regulation_references)
                    print(f"        Articles: {articles}")
    
    print("\n" + "=" * 70)
    print("✅ TEST PASSED!")
    print("=" * 70)
    
    # Return data for inspection
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ TEST FAILED!")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

    # Debug: Print raw recommendations
    print(f"\n🔍 DEBUG - Raw Recommendations:")
    for i, rec in enumerate(result.recommendations):
        print(f"\n   Recommendation {i+1}:")
        print(f"      Module: {rec.module_name}")
        print(f"      Quarter: {rec.quarter}")
        print(f"      Type: {type(rec.quarter)}")
        if hasattr(rec, 'regulation_references'):
            print(f"      Regulations: {rec.regulation_references}")
