import os

# Set of user ids that are completely blacklisted from interacting with the matrix.
blacklist = set()

# Inject tsars
matrix_tsars = {int(e) for e in os.getenv("MATRIX_TSARS", "").split(",") if e.strip()}

# Generic perms checker, dynamically operates in blacklist or whitelist mode 
# depending on whitelist length
def check_perms(user_id: int, elevated: bool = False) -> bool:
    if user_id in blacklist:
        return False
    
    return not (elevated and user_id not in matrix_tsars)
