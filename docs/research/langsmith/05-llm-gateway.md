# 05. LLM Gateway: what it does and how each request is handled

Sources: docs pages `llm-gateway`, `llm-gateway-how-it-works`, `llm-gateway-authentication`, `llm-gateway-api-formats`, `llm-gateway-direct-model-access`, `llm-gateway-fallbacks`, `llm-gateway-spend-policies`, `llm-gateway-rate-limit-policies`, `llm-gateway-model-access-policies`, `llm-gateway-data-policy`, `llm-gateway-decision-models`, `llm-gateway-credits`; headings only for `llm-gateway-provider-authentication`, `llm-gateway-header-policies`, `llm-gateway-model-configurations`, `llm-gateway-monitoring`, `llm-gateway-traces`, `llm-gateway-coding-agents`, `llm-gateway-admin-setup`. Read 2026-11-14. Status: **beta**.

## 1. Purpose

"The control layer between the agents and applications you run and the model providers your workspace has configured." Without it, each application holds its own provider keys and each provider account has its own spend and data controls. With it, **provider keys stay in LangSmith**, and policies apply to all callers in one place. Each call becomes a LangSmith trace.

## 2. The request pipeline (from `llm-gateway-how-it-works`)

1. **Authenticate and authorise** the caller from its LangSmith API key, including the `gateway:invoke` permission.
2. **Resolve the route** from the endpoint and model ID, including any fallback candidates.
3. **Load the upstream credential**: a workspace provider key, or a Gateway Credits credential.
4. **Evaluate pre-request policies**: spend, rate limits, model access.
5. **Translate the request** if the provider uses a different API format.
6. **Send upstream** and receive or stream the response.
7. **Translate the response** back to the client's format and restore any redaction placeholders.
8. **Return** the response, recording usage, cost, routing and policy metadata, and the trace.

**Direct model access** skips steps 5 and 7: the provider's native format passes through, but authentication, credentials, policies and tracing still apply.

## 3. Two authentication layers

- **Client to gateway:** a LangSmith API key. A **personal access token** (`lsv2_pt_`) carries its creator's permissions; a **service key** (`lsv2_sk_`) is not tied to a user. Keys need `gateway:invoke`. `LANGSMITH_GATEWAY_API_KEY` is the usual variable.
- **Gateway to provider:** a credential LangSmith holds. Usually a provider key stored as a **workspace secret**, or **Gateway Credits**. The client never holds it.

## 4. API formats

Three request and response formats share one gateway. The format and the provider are independent: a Chat Completions request can reach an Anthropic model, and the gateway translates it.

| Format | Base URL (US Cloud) | Endpoint | Typical clients |
|---|---|---|---|
| OpenAI Chat Completions | `https://gateway.smith.langchain.com/v1` | `POST /chat/completions` | OpenAI SDK, most compatible tools |
| Anthropic Messages | `https://gateway.smith.langchain.com` | `POST /v1/messages` | Anthropic SDK, Claude Code |
| OpenAI Responses | `https://gateway.smith.langchain.com/v1` | `POST /responses` | OpenAI Responses clients |

Direct access uses a provider-specific path under the regional gateway. LangChain and Deep Agents use direct access by default, through the `LANGSMITH_GATEWAY` environment setting.

## 5. Model fallbacks

- A chain has a **primary model**, **one to five fallbacks** (provider models or saved model configurations), and **trigger status codes**. Defaults include 408, 429, 500 and 503.
- Fallbacks are defined once in LangSmith; callers keep using the same endpoint and model ID.
- A request **blocked by a policy never triggers a fallback**, even though 429 is a default trigger.

## 6. Policies

Each policy has a **scope** (organisation, workspace, user or API key) and applies to callers in that scope.

| Policy | What it does | Blocked response |
|---|---|---|
| **Spend** | caps cost over a window (hourly, daily, weekly, monthly). Cost is recorded after a request completes, so the request that crosses the cap still succeeds and spend can exceed the cap by one request. Not applied to calls billed to a Claude subscription. | error "request blocked by gateway policies: <POLICY_NAME>" |
| **Rate limit** | caps requests or tokens in a rolling window; `Retry-After` gives seconds until reset | same error with 429 |
| **Model access** | allows or denies providers and models; with no policy everything is allowed | permission error |
| **Data** | **retention**: whether request and response bodies are written to the trace. **Protection**: which sensitive data (personal information, API keys) is scanned and redacted before the provider sees it, how long the scan may run, and whether the request proceeds if the scan times out | per policy |
| **Header-based** | policies keyed on request headers (page not read in full) | — |

Data protection is on by default for organisations with the entitlement; Enterprise customers without it see a "Request access" link.

## 7. Decision models

Classification and scoring endpoints that return structured answers instead of chat messages:
- **TypeSafe Jev** through the **System One** API at `/v1/systemone`, using a `TYPESAFE_API_KEY` workspace secret. Questions are `noul` (probability of yes), `choice` (one of given options) or `score` (against a rubric). The answer is keyed by question name. No streaming.
- **OpenAI decision models** through the OpenAI Decisions API at `/openai/v1/decisions`.

Both need a workspace-scoped key and the matching provider secret.

## 8. Credits and billing

**Gateway Credits** let a caller use LangChain-hosted models (for example `moonshotai/kimi-k2.6`) with only a LangSmith key. Model IDs are case-insensitive. Routing is by model ID: a hosted slug uses credits; a model ID with a configured provider prefix uses that workspace's key. Available on paid plans other than Enterprise.

## 9. What is traced

Every call is a trace with usage, cost, routing and policy metadata. Policy blocks are traced too, with the violation recorded, and they surface as **Engine issues** (file 07). Gateway traces have their own page (`llm-gateway-traces`) and monitoring page (`llm-gateway-monitoring`).

## 10. Where it runs

The US Cloud base URLs are shown above. The API-format page points to a "Use a regional gateway" section and a "Check availability" section for other regions, BYOC data planes and self-hosted installations; those regional lists were not read in full. Coding agents are supported through the Anthropic and OpenAI formats (`llm-gateway-coding-agents`).
