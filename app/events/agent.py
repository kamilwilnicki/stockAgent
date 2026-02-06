from  app.agent_func.prompts import guardrail_prompt, evaluator_prompt, worker_prompt, summary_prompt
import app.agent_func.mcp

from app.errors import AgentError
from app.types.state import State
from app.types.nodes_input import EvaluatorAnalysis, GuardRailAnalysis, SummaryAnalysis
from app.errors import AgentError

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
import os

class StockAgent:

    def __init__(self):

        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm = evaluator_llm.with_structured_output(EvaluatorAnalysis)

        guardrail_llm = ChatOpenAI(model="gpt-4o-mini")
        self.guardrail_llm = guardrail_llm.with_structured_output(GuardRailAnalysis)

        summary_llm = ChatOpenAI(model="gpt-5-mini")
        self.summary_llm = summary_llm.with_structured_output(SummaryAnalysis)


    async def tools_definition(self):
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)

        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        tools = toolkit.get_tools()
        env = os.environ.copy()
        env["SERPER_API_KEY"] = os.environ["SERPER_API_KEY"]
        mcp_client = MultiServerMCPClient({
            "simple-web-search-server": {
                "transport": "stdio",
                "command": "python",
                "args": ["-m","app.agent_func.mcp"],
                "env":env
            }
        }
        )

        tools_mcp = await mcp_client.get_tools()
        tools = tools + tools_mcp
        llm = ChatOpenAI(model="gpt-4o-mini")
        self.llm_with_tools = llm.bind_tools(tools)
        return tools
    async def graph_definition(self):

        def find_all_tool_messages(messages):
            tool_messages = []
            for message in reversed(messages):
                if isinstance(message, ToolMessage):
                    tool_messages.append(message)
                else:
                    break
            tool_messages = list(reversed(tool_messages))
            return tool_messages

        def guardrail(oldState: State) -> State:
            message = oldState['messages'][-1]
            system_prompt = guardrail_prompt()
            system_message = SystemMessage(content=system_prompt)
            
            messages = [system_message, message]
            response = self.guardrail_llm.invoke(messages)
            return {
                "stocks_list": response.list_of_stocks,
                "stock_analysis": [],
                "stock_completed": [False] * len(response.list_of_stocks),
                "analysis_completed": response.guardrail_analysis_completed,
                "reason_for_completed": response.guardrail_analysis_completed_reason,
                "wrong_evaluation": 0
            }
        def evaluator(oldState: State) -> State:
            stock_to_be_evaluated_index = oldState["stock_completed"].index(False)
            stock_to_be_evaluated=oldState["stocks_list"][stock_to_be_evaluated_index]
            current_stock_analysis=oldState["messages"][-1].content

            system_message, human_message = evaluator_prompt(oldState, stock_to_be_evaluated, current_stock_analysis)
            system_message = SystemMessage(content=system_message)
            human_message = HumanMessage(content=human_message)

            response = self.evaluator_llm.invoke([system_message, human_message])
            if response.analysis_completed:
                new_stock_completed = oldState["stock_completed"].copy()
                new_stock_completed[stock_to_be_evaluated_index] = True

                new_stock_analysis = oldState["stock_analysis"].copy()
                new_stock_analysis.append(current_stock_analysis)
                
                return {"feedback_on_work": "",
                        "stock_completed": new_stock_completed,
                        "stock_analysis": new_stock_analysis,
                        "wrong_evaluation": 0
                        }

            else:
                old_feedback = oldState.get("feedback_on_work","")

                return {"feedback_on_work": old_feedback + response.analysis_completed_reason,
                        "wrong_evaluation": oldState.get("wrong_evaluation",0)+1}

        def worker(oldState: State) -> State:

            if isinstance(oldState["messages"][-1], ToolMessage):
                current_messages_worker = oldState['current_messages_worker'] + find_all_tool_messages(oldState["messages"])
                response = self.llm_with_tools.invoke(current_messages_worker)
                current_messages_worker = current_messages_worker + [response]
                return {"messages": [response],
                        "current_messages_worker":current_messages_worker}



            stock_to_be_analysed_index = oldState["stock_completed"].index(False)

            stock_to_be_analysed=oldState["stocks_list"][stock_to_be_analysed_index]
            system_message, human_message = worker_prompt(stock_to_be_analysed)
            feedback_on_worker = oldState.get("feedback_on_work","")
            if feedback_on_worker != "":
                human_message += f"""Last time you thought that you did the best analysis but you lacked some specific info provided below: \n {feedback_on_worker}
                Create from the begging the analysis with the information that you provided before and with additional info that you will search specified by the feedback."""

            system_message = SystemMessage(content=system_message)
            human_message = HumanMessage(content=human_message)

            systemMessagePresent = False
            for message in oldState["current_messages_worker"]:
                if isinstance(message, SystemMessage):
                    systemMessagePresent=True   

            if systemMessagePresent:
                messages = oldState["current_messages_worker"] + [human_message]
                response = self.llm_with_tools.invoke(messages)
                response= messages + [response]
            else:
                messages=[system_message, human_message]
                response = self.llm_with_tools.invoke(messages)
                response=[system_message,human_message,response]
            
            return {
                "messages":response,
                "current_messages_worker":response
            }

        def summary(oldState: State) -> State:
            stocks_list = oldState["stocks_list"]
            stock_completed = oldState["stock_completed"]
            stock_analysis = oldState['stock_analysis']

            if len(stocks_list) == sum(stock_completed):
                system_message, human_message = summary_prompt()

                system_prompt=SystemMessage(content=system_message)
                human_prompt= human_message
                for index, analysis in enumerate(stock_analysis):
                    human_prompt+=f"""
                    Stock: {stocks_list[index]}
                    {analysis}
                    """
                messages = [system_prompt, HumanMessage(human_prompt)]
                response = self.summary_llm.invoke(messages)
                
                return {"messages": [AIMessage(response.summary)],
                        "analysis_completed":True,
                        "reason_for_completed":"All stocks are analysed"}
            return {"current_messages_worker":[]}

        def guardrail_router(state: State) -> str:
            if state["analysis_completed"]:
                return "END"
            else:
                return "summary"

        def summary_router(state:State) -> str:
            if state["analysis_completed"]:
                return "END"
            else:
                return "worker"
        def evaluator_router(state: State) -> str:
            if state["feedback_on_work"] != "":
                return "worker"
            else:
                return "summary"
        def worker_router(state: State) -> str:
            last_message = state["messages"][-1]
            
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            else:
                return "evaluator" 

        graph = StateGraph(State)

        tools = await self.tools_definition()
        
        graph.add_node('guardrail',guardrail)
        graph.add_node("summary", summary)
        graph.add_node("evaluator",evaluator)
        graph.add_node("worker",worker)
        graph.add_node("tools",ToolNode(tools))

        graph.add_edge(START, 'guardrail')
        graph.add_conditional_edges("guardrail", guardrail_router, {"END":END, "summary":"summary"})
        graph.add_conditional_edges("summary", summary_router, {"END":END, "worker":"worker"})
        graph.add_conditional_edges("worker", worker_router, {"tools": "tools", "evaluator": "evaluator"})
        graph.add_edge("tools","worker")
        graph.add_conditional_edges("evaluator",evaluator_router,{"worker":"worker","summary":"summary"})
        graph.add_edge('guardrail', END)

        graph_compiled = graph.compile()
        return graph_compiled

    async def agent_inference(self, message):
        try:
            graph_compiled = await self.graph_definition()
            result = await graph_compiled.ainvoke({"messages":[HumanMessage(content=message)], "analysis_completed":False}, {"recursion_limit":150})
            result = str(result["messages"][-1].content)
            return result
        except Exception as e:
            print(e)
            raise AgentError("Right now the agentic AI is not available, please try later")
        
