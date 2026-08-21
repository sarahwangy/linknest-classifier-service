# Must stay in sync with linknest's lib/claude.ts CATEGORIES list —
# the fine-tuned model's label set has to match what Linknest already tags
# bookmarks with, since training data comes from those existing aiCategory values.
CATEGORIES = [
    "Technology", "Science", "Business", "Finance", "Health", "Entertainment",
    "Sports", "Politics", "Education", "Design", "Food", "Travel",
    "News", "Reference", "Shopping", "Social", "Productivity", "Uncategorized",
]

LABEL2ID = {label: i for i, label in enumerate(CATEGORIES)}
ID2LABEL = {i: label for i, label in enumerate(CATEGORIES)}
