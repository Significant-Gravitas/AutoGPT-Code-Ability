MODULE_INTO_INTO_DATABASE = """generate a Prisma schema file with the following product spec. Make sure it covers all requirements, roles, Q&A, and auth

Your needed auth roles are: {needed_auth_roles}
the available modules are: {modules}


Reply in the following format; do not add any extra information
<think>
thoughts about the task, including things that should be included. Notate each model with what modules from the spec are relevant to it
</think>
<anti_think>
thoughts about what shouldn't be included, bad plans and generally things that should be avoided
</anti_think>
<plan>
What do you plan to do focusing on the top-level models? Start with the required enums, then go to the models. Consider the key relationships and core entities. Then, break down each top-level model into relevant details about it. Notate each model with what modules from the spec are relevant to it
</plan>
<refine>
refine the plan, and point out issues and gaps. if there's functionality that can't be accomplished with the plan, outline it here. Anything omitted here won't be included in the final product, so it needs to be through. Keep an eye out for things that can be converted to enums or models that are needed
</refine>
<pre_answer>
the schema improved based on the refined output. Thoroughly outline each model with the fields it needs
</pre_answer>
<pre_answer_issues>
list issues with pre_answer. add solutions to them in line
</pre_answer_issues>
<full_schema>
```prisma
improve the schema from pre_answer to include any additional fields needed. output a whole prisma schema. Anything ommited here won't be included in the final product so it needs to be through.

write the combined and full schema here with comments not including the database and generator
```
</full_schema>
<database_schema>
  <name>Name of the Schema</name>
  <description>Description of the Schema</description>
  <tables>
    <table>
      <name>The name of the prisma table</name>
      <description>The description of the prisma table</description>
      <definition>The string prisma definition for the schema</definition>
    </table>
    ... repeat for all tables in full_schema making sure each is fully defined and valid prisma schemas
  </tables>
</database_schema>
<conclusions>
any concluding thoughts
</conclusions>


Human: {product_spec}

Assistant: <think>
Relational data models will be needed to represent entities as well as defining relationships between them.

The backend will likely consist of a REST API layer handling requests from frontend. Services exposed via that API will power the various use cases.

For all schemas I provide, I need to make sure they are full schemas with no removals nor shortenings"""
