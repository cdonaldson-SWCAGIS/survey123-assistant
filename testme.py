from xlsform_orm import Survey, Question, QuestionGroup, Choice, QuestionTypes

# Create a simple survey
survey = Survey(
    name="my_survey",
    label="My Survey",
    items=[
        Question(
            type=QuestionTypes.text,
            name="name",
            label="What is your name?"
        ),
        Question(
            type=QuestionTypes.select_one,
            name="color",
            label="Favorite color?",
            choices=[
                Choice(value="r", label="Red"),
                Choice(value="b", label="Blue"),
                Choice(value="g", label="Green"),
            ]
        )
    ]
)

# Export to Excel
survey.save_to_excel("my_survey.xlsx")

# Export to YAML
survey.save_to_yaml("my_survey.yaml")