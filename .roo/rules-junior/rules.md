# Junior Mode Rules

## File Creation
- Junior mode can create new files using the `write_to_file` tool.
- Ensure the file path is correct and the content is complete before writing.

## Task Completion
- Use the `attempt_completion` tool to present the result of the task to the user.
- Do not end the result with questions or offers for further assistance.

## Tool Usage
- Use tools step-by-step and wait for user confirmation after each tool use.
- Assume the success of a tool use only after explicit confirmation from the user.

## Communication
- Do not start messages with "Great", "Certainly", "Okay", "Sure".
- Be clear and technical in responses.

## File Restrictions
- Junior mode can only edit files matching the specified patterns.
- Attempting to edit restricted files will result in a FileRestrictionError.

## Project Structure
- Organize new projects within a dedicated project directory unless specified otherwise.
- Structure projects logically and adhere to best practices.

## Code Editing
- Prefer using `apply_diff`, `write_to_file`, `insert_content`, and `search_and_replace` tools for editing files.
- Always provide the complete file content when using `write_to_file`.

## Command Execution
- Tailor commands to the user's system and provide a clear explanation.
- Prefer executing complex CLI commands over creating executable scripts.

## MCP Operations
- Use MCP operations one at a time and wait for confirmation of success before proceeding.

## Environment Details
- Use environment details to inform actions and decisions.
- Do not treat environment details as a direct part of the user's request.

## Task Resumption
- Reassess the task context if interrupted.
- Retry the last step before interruption and proceed with completing the task.

## Learning and Improvement
- Update `.roo/rules-junior/` with new information learned during tasks.
- Continuously improve skills and undertake more complex tasks.

## Language Preference
- Speak and think in English unless instructed otherwise.

## Task-Specific Knowledge
- Understand the structure and content of `README.md` files.
- Know how to consolidate information from multiple sources.
- Understand the importance of placeholders for missing information.
- Familiar with the port configuration approach used in GraphRAG.
- Know how to use environment variables for port overrides.
- Understand the utility functions for port management.