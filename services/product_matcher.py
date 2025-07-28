import asyncio
from typing import Optional, Dict, List
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process
import re
from datetime import datetime

# Import the models
from models.product import Product, ProductMapping

class ProductMatcher:
    def __init__(self, db: Session):
        self.db = db
        self.confidence_threshold = 0.8
    
    async def find_best_match(
        self, 
        name: str, 
        sku: Optional[str] = None,
        platform: str = "unknown",
        external_id: Optional[str] = None
    ) -> Dict:
        """
        Advanced product matching using multiple strategies:
        1. Exact SKU match (highest priority)
        2. Fuzzy name matching with normalization
        3. Previous mapping lookup
        4. Manual review queue for low confidence
        """
        
        # Strategy 1: Exact SKU match
        if sku:
            exact_match = self.db.query(Product).filter(
                Product.sku == sku
            ).first()
            if exact_match:
                await self._save_mapping(exact_match.id, name, sku, platform, external_id)
                return {
                    "product_id": exact_match.id,
                    "confidence": 1.0,
                    "match_type": "sku_exact",
                    "matched_name": exact_match.master_name
                }
        
        # Strategy 2: Check existing mappings
        existing_mapping = self.db.query(ProductMapping).filter(
            ProductMapping.platform == platform,
            ProductMapping.external_id == external_id
        ).first()
        if existing_mapping:
            return {
                "product_id": existing_mapping.product_id,
                "confidence": 0.95,
                "match_type": "mapping_exists",
                "matched_name": existing_mapping.product.master_name
            }
        
        # Strategy 3: Fuzzy name matching
        normalized_name = self._normalize_name(name)
        all_products = self.db.query(Product).filter(Product.active == True).all()
        
        best_match = None
        best_score = 0
        
        for product in all_products:
            normalized_product_name = self._normalize_name(product.master_name)
            
            # Use multiple fuzzy matching algorithms
            scores = [
                fuzz.ratio(normalized_name, normalized_product_name),
                fuzz.partial_ratio(normalized_name, normalized_product_name),
                fuzz.token_sort_ratio(normalized_name, normalized_product_name),
                fuzz.token_set_ratio(normalized_name, normalized_product_name)
            ]
            
            # Weighted average (token_set_ratio gets higher weight)
            combined_score = (scores[0] + scores[1] + scores[2] + scores[3] * 2) / 5
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = product
        
        confidence = best_score / 100.0
        
        # Auto-approve high confidence matches
        if confidence >= self.confidence_threshold and best_match:
            await self._save_mapping(best_match.id, name, sku, platform, external_id)
            return {
                "product_id": best_match.id,
                "confidence": confidence,
                "match_type": "fuzzy_auto",
                "matched_name": best_match.master_name
            }
        
        # Queue for manual review
        elif confidence >= 0.5 and best_match:
            await self._queue_for_review(name, sku, platform, external_id, best_match, confidence)
            return {
                "product_id": None,
                "confidence": confidence,
                "match_type": "manual_review_required",
                "suggested_match": best_match.master_name,
                "suggested_id": best_match.id
            }
        
        # No good match found - create new product
        else:
            await self._queue_for_new_product(name, sku, platform, external_id)
            return {
                "product_id": None,
                "confidence": 0.0,
                "match_type": "new_product_required",
                "message": "No suitable match found. Queued for new product creation."
            }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize product names for better matching"""
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove common variations
        replacements = {
            'knightsbridge': 'knights bridge',
            'nice bridge': 'knights bridge',
            '&': 'and',
            '+': 'and',
            '-': ' ',
            '_': ' ',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces and special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    async def _save_mapping(self, product_id: str, name: str, sku: str, platform: str, external_id: str):
        """Save successful product mapping"""
        mapping = ProductMapping(
            product_id=product_id,
            platform=platform,
            external_id=external_id,
            external_name=name,
            last_synced=datetime.now()
        )
        self.db.add(mapping)
        self.db.commit()
    
    async def _queue_for_review(self, name: str, sku: str, platform: str, external_id: str, suggested_match, confidence: float):
        """Queue uncertain matches for manual review"""
        # This would integrate with your notification system
        pass
    
    async def _queue_for_new_product(self, name: str, sku: str, platform: str, external_id: str):
        """Queue for new product creation"""
        # This would create a pending product entry
        pass