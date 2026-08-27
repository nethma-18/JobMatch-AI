async def create_indexes(db):
    """Run once on startup to create all needed indexes."""

    # Users — unique email
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("role")

    # Seeker & HR profiles
    await db["seeker_profiles"].create_index("user_id")
    await db["hr_profiles"].create_index("user_id")

    # Future collections (safe to create early)
    await db["resumes"].create_index("user_id")
    await db["job_posts"].create_index("hr_id")
    await db["job_posts"].create_index("status")
    await db["applications"].create_index("seeker_id")
    await db["applications"].create_index("job_id")
    await db["interviews"].create_index("job_id")
    await db["interviews"].create_index("candidate_id")
    await db["rankings"].create_index("job_id")
    await db["shortlists"].create_index("job_id")
    await db["validation_queue"].create_index("user_id")
    await db["validation_queue"].create_index("validation_status")
    await db["training_pool"].create_index("source")
    await db["notifications"].create_index([("user_id", 1), ("read", 1)])

    print("[OK] MongoDB indexes created")