from skill_server.skills import question_calibrator, rubric_builder

skill_registry = {
    "question_calibrator": question_calibrator.run,
    "rubric_builder": rubric_builder.run,
}
