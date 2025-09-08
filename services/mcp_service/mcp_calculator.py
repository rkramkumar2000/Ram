"""
MCP (Model Context Protocol) Calculator Service
===============================================

This service provides premium and claim calculation tools using the Model Context Protocol.
It includes hardcoded calculation logic for demonstration purposes.

Features:
- Premium calculation based on policy type, age, coverage amount
- Claim processing and calculation
- MCP-compliant tool interfaces
- FastAPI web interface for easy testing

Author: Insurance Policy RAG System
Version: 1.0.0
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PremiumCalculator:
    """Premium calculation engine with hardcoded rates"""
    
    # Base rates by policy type (monthly premium per $1000 coverage)
    BASE_RATES = {
        "life_insurance": {
            "term": 0.50,
            "whole": 2.50,
            "universal": 1.80
        },
        "auto_insurance": {
            "liability": 0.80,
            "comprehensive": 1.20,
            "collision": 1.00
        },
        "health_insurance": {
            "basic": 3.50,
            "premium": 5.80,
            "platinum": 8.20
        },
        "home_insurance": {
            "basic": 0.60,
            "comprehensive": 1.10,
            "premium": 1.50
        }
    }
    
    # Age multipliers
    AGE_MULTIPLIERS = {
        (18, 25): 1.50,  # Higher risk
        (26, 35): 1.20,
        (36, 45): 1.00,  # Base rate
        (46, 55): 1.30,
        (56, 65): 1.80,
        (66, 100): 2.50  # Highest risk
    }
    
    # Risk factor multipliers
    RISK_FACTORS = {
        "smoker": 1.75,
        "high_risk_occupation": 1.40,
        "poor_health": 1.60,
        "good_driver": 0.85,
        "safe_neighborhood": 0.90,
        "security_system": 0.95
    }
    
    @classmethod
    def calculate_premium(
        cls, 
        policy_type: str, 
        sub_type: str, 
        coverage_amount: float, 
        customer_age: int,
        risk_factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate insurance premium based on input parameters"""
        
        try:
            # Validate inputs
            if policy_type not in cls.BASE_RATES:
                raise ValueError(f"Invalid policy type: {policy_type}")
            
            if sub_type not in cls.BASE_RATES[policy_type]:
                raise ValueError(f"Invalid sub-type: {sub_type} for {policy_type}")
            
            if coverage_amount <= 0:
                raise ValueError("Coverage amount must be positive")
            
            if customer_age < 18 or customer_age > 100:
                raise ValueError("Customer age must be between 18 and 100")
            
            # Get base rate
            base_rate = cls.BASE_RATES[policy_type][sub_type]
            
            # Calculate base premium
            base_premium = (coverage_amount / 1000) * base_rate
            
            # Apply age multiplier
            age_multiplier = 1.0
            for age_range, multiplier in cls.AGE_MULTIPLIERS.items():
                if age_range[0] <= customer_age <= age_range[1]:
                    age_multiplier = multiplier
                    break
            
            # Apply risk factors
            risk_multiplier = 1.0
            applied_factors = []
            if risk_factors:
                for factor in risk_factors:
                    if factor in cls.RISK_FACTORS:
                        risk_multiplier *= cls.RISK_FACTORS[factor]
                        applied_factors.append(factor)
            
            # Calculate final premium
            final_premium = base_premium * age_multiplier * risk_multiplier
            
            # Round to 2 decimal places
            final_premium = round(final_premium, 2)
            
            calculation_details = {
                "policy_type": policy_type,
                "sub_type": sub_type,
                "coverage_amount": coverage_amount,
                "customer_age": customer_age,
                "base_rate": base_rate,
                "base_premium": round(base_premium, 2),
                "age_multiplier": age_multiplier,
                "risk_multiplier": round(risk_multiplier, 2),
                "applied_risk_factors": applied_factors,
                "monthly_premium": final_premium,
                "annual_premium": round(final_premium * 12, 2),
                "calculation_date": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "premium_calculation": calculation_details,
                "message": f"Premium calculated successfully: ${final_premium}/month"
            }
            
        except Exception as e:
            logger.error(f"Premium calculation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Premium calculation failed"
            }

class ClaimCalculator:
    """Claim processing and calculation engine"""
    
    # Claim types and their typical processing rules
    CLAIM_TYPES = {
        "life_insurance": {
            "death_benefit": {"payout_percentage": 100, "processing_days": 30},
            "disability": {"payout_percentage": 75, "processing_days": 45}
        },
        "auto_insurance": {
            "collision": {"deductible": 500, "max_coverage": 50000, "processing_days": 14},
            "comprehensive": {"deductible": 250, "max_coverage": 75000, "processing_days": 10},
            "liability": {"deductible": 0, "max_coverage": 100000, "processing_days": 21}
        },
        "health_insurance": {
            "medical": {"deductible": 1000, "copay_percentage": 20, "processing_days": 7},
            "prescription": {"deductible": 0, "copay_percentage": 10, "processing_days": 3},
            "emergency": {"deductible": 500, "copay_percentage": 10, "processing_days": 5}
        },
        "home_insurance": {
            "fire_damage": {"deductible": 1000, "max_coverage": 500000, "processing_days": 30},
            "theft": {"deductible": 500, "max_coverage": 100000, "processing_days": 21},
            "water_damage": {"deductible": 750, "max_coverage": 200000, "processing_days": 25}
        }
    }
    
    @classmethod
    def calculate_claim(
        cls,
        policy_type: str,
        claim_type: str,
        claim_amount: float,
        policy_coverage: float,
        policy_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate claim payout and processing details"""
        
        try:
            # Validate inputs
            if policy_type not in cls.CLAIM_TYPES:
                raise ValueError(f"Invalid policy type: {policy_type}")
            
            if claim_type not in cls.CLAIM_TYPES[policy_type]:
                raise ValueError(f"Invalid claim type: {claim_type} for {policy_type}")
            
            if claim_amount <= 0:
                raise ValueError("Claim amount must be positive")
            
            if policy_coverage <= 0:
                raise ValueError("Policy coverage must be positive")
            
            claim_rules = cls.CLAIM_TYPES[policy_type][claim_type]
            
            # Calculate payout based on claim type
            if "payout_percentage" in claim_rules:
                # Life insurance style - percentage of coverage
                payout_amount = min(claim_amount, policy_coverage * (claim_rules["payout_percentage"] / 100))
                deductible = 0
                
            else:
                # Other insurance types - deductible based
                deductible = claim_rules.get("deductible", 0)
                max_coverage = claim_rules.get("max_coverage", policy_coverage)
                copay_percentage = claim_rules.get("copay_percentage", 0)
                
                # Apply deductible
                after_deductible = max(0, claim_amount - deductible)
                
                # Apply copay
                after_copay = after_deductible * (1 - copay_percentage / 100)
                
                # Apply coverage limits
                payout_amount = min(after_copay, max_coverage, policy_coverage)
            
            # Round to 2 decimal places
            payout_amount = round(payout_amount, 2)
            
            # Calculate processing timeline
            processing_days = claim_rules.get("processing_days", 14)
            estimated_completion = datetime.now().replace(
                day=datetime.now().day + processing_days
            ).date().isoformat()
            
            # Determine claim status
            approval_status = "approved" if payout_amount > 0 else "denied"
            if claim_amount > policy_coverage:
                approval_status = "partially_approved"
            
            claim_details = {
                "policy_type": policy_type,
                "claim_type": claim_type,
                "claim_amount": claim_amount,
                "policy_coverage": policy_coverage,
                "deductible": deductible,
                "payout_amount": payout_amount,
                "approval_status": approval_status,
                "processing_days": processing_days,
                "estimated_completion": estimated_completion,
                "claim_id": f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "processing_date": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "claim_calculation": claim_details,
                "message": f"Claim processed: ${payout_amount} approved for payout"
            }
            
        except Exception as e:
            logger.error(f"Claim calculation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Claim calculation failed"
            }

class MCPCalculatorTools:
    """MCP-compliant tool definitions for insurance calculations"""
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Return list of available MCP tools"""
        return [
            {
                "name": "calculate_premium",
                "description": "Calculate insurance premium based on policy type, coverage, and customer details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_type": {
                            "type": "string",
                            "enum": ["life_insurance", "auto_insurance", "health_insurance", "home_insurance"],
                            "description": "Type of insurance policy"
                        },
                        "sub_type": {
                            "type": "string",
                            "description": "Sub-type of insurance (e.g., term, whole, comprehensive)"
                        },
                        "coverage_amount": {
                            "type": "number",
                            "minimum": 1,
                            "description": "Coverage amount in dollars"
                        },
                        "customer_age": {
                            "type": "integer",
                            "minimum": 18,
                            "maximum": 100,
                            "description": "Customer age in years"
                        },
                        "risk_factors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of risk factors (smoker, high_risk_occupation, etc.)"
                        }
                    },
                    "required": ["policy_type", "sub_type", "coverage_amount", "customer_age"]
                }
            },
            {
                "name": "calculate_claim",
                "description": "Process and calculate claim payout amount",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_type": {
                            "type": "string",
                            "enum": ["life_insurance", "auto_insurance", "health_insurance", "home_insurance"],
                            "description": "Type of insurance policy"
                        },
                        "claim_type": {
                            "type": "string",
                            "description": "Type of claim (collision, medical, fire_damage, etc.)"
                        },
                        "claim_amount": {
                            "type": "number",
                            "minimum": 1,
                            "description": "Claimed amount in dollars"
                        },
                        "policy_coverage": {
                            "type": "number",
                            "minimum": 1,
                            "description": "Policy coverage limit in dollars"
                        }
                    },
                    "required": ["policy_type", "claim_type", "claim_amount", "policy_coverage"]
                }
            },
            {
                "name": "get_policy_info",
                "description": "Get information about available policy types and coverage options",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "enum": ["policy_types", "claim_types", "risk_factors"],
                            "description": "Type of information to retrieve"
                        }
                    },
                    "required": ["info_type"]
                }
            }
        ]
    
    @staticmethod
    async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool with given arguments"""
        
        try:
            if tool_name == "calculate_premium":
                return PremiumCalculator.calculate_premium(
                    policy_type=arguments["policy_type"],
                    sub_type=arguments["sub_type"],
                    coverage_amount=arguments["coverage_amount"],
                    customer_age=arguments["customer_age"],
                    risk_factors=arguments.get("risk_factors")
                )
            
            elif tool_name == "calculate_claim":
                return ClaimCalculator.calculate_claim(
                    policy_type=arguments["policy_type"],
                    claim_type=arguments["claim_type"],
                    claim_amount=arguments["claim_amount"],
                    policy_coverage=arguments["policy_coverage"]
                )
            
            elif tool_name == "get_policy_info":
                info_type = arguments["info_type"]
                
                if info_type == "policy_types":
                    return {
                        "success": True,
                        "data": {
                            "policy_types": list(PremiumCalculator.BASE_RATES.keys()),
                            "sub_types": PremiumCalculator.BASE_RATES
                        }
                    }
                elif info_type == "claim_types":
                    return {
                        "success": True,
                        "data": {"claim_types": ClaimCalculator.CLAIM_TYPES}
                    }
                elif info_type == "risk_factors":
                    return {
                        "success": True,
                        "data": {"risk_factors": list(PremiumCalculator.RISK_FACTORS.keys())}
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage and testing
if __name__ == "__main__":
    print("MCP Calculator Service - Testing")
    print("=" * 50)
    
    # Test premium calculation
    print("\n1. Testing Premium Calculation:")
    premium_result = PremiumCalculator.calculate_premium(
        policy_type="life_insurance",
        sub_type="term",
        coverage_amount=100000,
        customer_age=35,
        risk_factors=["smoker"]
    )
    print(json.dumps(premium_result, indent=2))
    
    # Test claim calculation
    print("\n2. Testing Claim Calculation:")
    claim_result = ClaimCalculator.calculate_claim(
        policy_type="auto_insurance",
        claim_type="collision",
        claim_amount=8000,
        policy_coverage=50000
    )
    print(json.dumps(claim_result, indent=2))
    
    # Test MCP tools
    print("\n3. Testing MCP Tools:")
    tools = MCPCalculatorTools.get_available_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")
