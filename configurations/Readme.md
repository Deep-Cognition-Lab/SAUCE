# Configurations folder

This folder exists for you to save you configurations.

This folder is ignored from the VCS but if there an amazing or a good example of configuration that should be track, go a head and track it 💪🏻

## Configuration format

The configuration is currently support only JSON format, but (yaml is planned to be supported in the near future)

## Format

example

```json
{
  "persons": [
    {
      "class": "", // Person type that will be used
      "name": "", // Persons name
      "background_story": "" // person backstory
      // any other keyword argument unique to given Person type are added here
    }
  ],
  "host": {
    "class": "" // host class that will be used
    // any other keyword argument unique to given Host type are added here
  },
  "endType": {
    "class": "iteration" // end type class that will be used
    // any other keyword argument unique to given EndType type are added here
  },
  "experiment": {
    "scenario": "", // the scanario the experimant is running in (might be used by the created "person")

    "survey_questions": [
      {
        // survey question id, it will added to the experiment result
        "id": "",
        // what question should be asked
        "question": "",
        // in what iteration ask the question accepted values are 1.list of unsigned int or -1(indicating the last iteration) 2.The str always
        "iterations":"always" | [1, 5, 4],

      }
    ]
  }
}
```
