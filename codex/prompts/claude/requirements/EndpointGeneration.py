ENDPOINT_PARAMS_GEN = """You are a premier system architect and API designer. You need to define the inputs and outputs of an API endpoint

Here's some context
{spec}

Your available database models are: {db_models}

Reply only with this object model in mind using an XML format
```python

class Parameter(BaseModel):
    name: str
    param_type: str
    description: str


class RequestModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

class ResponseModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

```
Converted to XML:
<think>general thoughts about the task</think>
<db_models_needed>
  [a, list, of, db, models, used, only, from, the, prisma, file]
</db_models_needed>
<new_api_models>
 <model>
  <name>NameOfTheModel</name>
  <description>A Description Of the Model</description>
  <params>
    <param>
      <name>a parameter name</name>
      <param_type>the type of the param</param_type>
      <description>a description of the parameter</description>
    </param>
    ... repeat for all parameters
  </params>
 <model>
</new_api_models>
<api_endpoint>
 <request_model>
    <name>Request model name</name>
    <description> the description of the request model, including any additional context that's important/relevant/weird/cool/useful</description>
    <params>
      <param>
        <name>a parameter name</name>
        <param_type>the type of the param</param_type>
        <description>a description of the parameter</description>
      </param>
      ... repeat for all parameters
    </params>
  </request_model>
  <response_model>
    <name>response model name</name>
    <description> the description of the response model, including any additional context that's important/relevant/weird/cool/useful</description>
    <params>
      <param>
        <name>a parameter name</name>
        <param_type>the type of the param</param_type>
        <description>a description of the parameter</description>
      </param>
      ... repeat for all parameters
    </params>
  </response_model>
</api_endpoint>
<end_thoughts>
closing thoughts on the matter
</end_thoughts>



Example for `GET /user_id_by_discord_id/{id}`:
<think>I'll need to leverage the context provided to ensure the UserDTO object makes sense. I'll also provide any models needed for my return types if they aren't based on the db model from prisma</think>
<db_models_needed>
  [User]
</db_models_needed>
<new_api_models>
  N/A
</new_api_models>
<api_endpoint>
 <request_model>
    <name>user_by_discord_id_input</name>
    <description>This request only requires the user's id from the User object as defined in the Users table. If there's anything else, its an error</description>
    <params>
      <param>
        <name>id</name>
        <param_type>str</param_type>
        <description>the discord user id to look the user up by</description>
      </param>
    </params>
  </request_model>
  <response_model>
    <name>user_by_discord_id_output</name>
    <description> will output the full user object minus a few secrets as the UserDTO</description>
    <params>
      <param>
        <name>user</name>
        <param_type>User</param_type>
        <description>the UserDTO</description>
      </param>
    </params>
  </response_model>
</api_endpoint>
<end_thoughts>
wow that was fun
</end_thoughts>

Human: {endpoint_and_module_repr}\n\n
Assistant: <think>My Available DB Models are {db_models}. If there are no params, I'll put N/A in the params tag rather than leaving it blank"""
