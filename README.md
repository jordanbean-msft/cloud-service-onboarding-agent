# cloud-service-onboarding-agent

![architecture](./.img/architecture.png)

## Cloud Service Onboarding Agent process
```mermaid
stateDiagram-v2
    [*] -->  request_for_new_cloud_service_onboarding
    request_for_new_cloud_service_onboarding --> API
    API --> cloud_service_onboarding_process
    state cloud_service_onboarding_process {
        [*] --> retrieve_public_documentation

        retrieve_public_documentation --> retrieve_security_documentation
        retrieve_security_documentation --> make_security_recommendations
        make_security_recommendations --> build_azure_policy
        build_azure_policy --> write_terraform
    }
    write_terraform --> update_ui
    update_ui --> [*]
```

## Disclaimer

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure subscription & resource group
- [Python](https://www.python.org/downloads/)

## Azure Resources needed

- Azure AI Foundry Service
  - OpenAI model (gpt-4o)
  - Grounding with Bing
  - Vector Store
  - AI Agent service
- Azure App Service
- Azure Storage Account


## Deployment

## Links
