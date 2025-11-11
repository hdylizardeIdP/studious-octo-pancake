import re
from typing import List, Dict, Optional


class ItemExtractor:
    """Extracts grocery items from text"""

    # Common grocery categories for classification
    CATEGORIES = {
        'produce': ['apple', 'banana', 'orange', 'lettuce', 'tomato', 'potato', 'onion', 'carrot', 'broccoli', 'spinach'],
        'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'eggs'],
        'meat': ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'bacon', 'sausage'],
        'bakery': ['bread', 'bagel', 'muffin', 'croissant', 'buns', 'rolls'],
        'pantry': ['rice', 'pasta', 'flour', 'sugar', 'salt', 'pepper', 'oil', 'sauce', 'cereal'],
        'beverages': ['coffee', 'tea', 'juice', 'soda', 'water', 'beer', 'wine'],
        'snacks': ['chips', 'crackers', 'cookies', 'candy', 'nuts', 'popcorn'],
        'frozen': ['ice cream', 'frozen pizza', 'frozen vegetables', 'frozen fruit'],
        'cleaning': ['soap', 'detergent', 'bleach', 'sponge', 'paper towels', 'toilet paper'],
    }

    def extract_items(self, text: str) -> List[Dict[str, any]]:
        """
        Extract grocery items from text
        Handles various formats:
        - Simple lists (one item per line)
        - Numbered lists (1. item, 2. item)
        - Bulleted lists (- item, * item, • item)
        - Quantity + item (2 apples, 1 lb chicken)
        """
        items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract item from various formats
            item_text = self._extract_item_text(line)

            if item_text:
                # Detect category
                category = self._detect_category(item_text)

                items.append({
                    'name': item_text,
                    'category': category,
                    'original': line
                })

        return items

    def _extract_item_text(self, line: str) -> Optional[str]:
        """Extract clean item text from a line"""
        # Remove common list markers
        patterns = [
            r'^\d+[\.\)]\s*',  # 1. or 1)
            r'^[-*•]\s*',       # -, *, •
            r'^\[\s*\]\s*',     # [ ]
            r'^\(\s*\)\s*',     # ( )
        ]

        for pattern in patterns:
            line = re.sub(pattern, '', line)

        # Remove quantity patterns (optional)
        # Examples: "2 apples", "1 lb chicken", "3 bags chips"
        line = re.sub(r'^\d+\s*(lb|lbs|oz|kg|g|bags?|cans?|bottles?|boxes?|packs?)?\s*', '', line, flags=re.IGNORECASE)

        line = line.strip()

        # Skip if too short or too long
        if len(line) < 2 or len(line) > 100:
            return None

        # Skip if it's a header or title (all caps, or contains certain keywords)
        if line.isupper() and len(line) > 15:
            return None

        skip_keywords = ['grocery', 'list', 'shopping', 'store', 'items', 'total', 'date']
        if any(keyword in line.lower() for keyword in skip_keywords) and len(line.split()) <= 3:
            return None

        return line

    def _detect_category(self, item_text: str) -> Optional[str]:
        """Detect item category based on keywords"""
        item_lower = item_text.lower()

        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in item_lower:
                    return category

        return None

    def extract_from_voice(self, text: str) -> List[Dict[str, any]]:
        """
        Extract items from voice transcription
        Voice input often comes as comma-separated or 'and' separated
        Example: "apples, bananas, milk and cheese"
        """
        # Split by common separators
        text = text.replace(' and ', ', ')
        items_list = re.split(r'[,;]', text)

        items = []
        for item_text in items_list:
            item_text = item_text.strip()
            if item_text and len(item_text) > 1:
                category = self._detect_category(item_text)
                items.append({
                    'name': item_text,
                    'category': category,
                    'original': item_text
                })

        return items
