# Set of user ids that are completely blacklisted from interacting with the matrix.
blacklist = set()

# Set of user ids that are allowed to interact with the matrix.
# When len > 0, the bot will act in whitelist ONLY mode. When empty it will operate on a blacklist basis.
whitelist = set()

# True if there are entries
whitelist_on = bool(whitelist)

# Generic perms checker, dynamically operates in blacklist or whitelist mode 
# depending on whitelist length
def check_perms(user_id: int) -> bool:
    if user_id in blacklist:
        return False

    if whitelist_on:
        return user_id in whitelist

    return True
