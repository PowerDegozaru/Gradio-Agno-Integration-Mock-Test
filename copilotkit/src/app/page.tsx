"use client";

import { Tool } from "@/components/tool";
import { CatchAllActionRenderProps, useCopilotAction } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotSidebar } from "@copilotkit/react-ui";
import { useState } from "react";

export default function CopilotKitPage() {
  const [themeColor] = useState("#6366f1");

  return (
    <main style={{ "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties}>
      <YourMainContent themeColor={themeColor} />
      {/* <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "Investment Analyst",
          initial: "👋 Hi there! I'm your AI investment analyst powered by Agno. I can help you research stocks, analyze market data, and provide investment insights.\n\nTry asking me about:\n- **Stock Analysis**: \"What's the current price of AAPL?\"\n- **Fundamentals**: \"Show me the fundamentals for Tesla\"\n- **Recommendations**: \"What do analysts recommend for Microsoft?\"\n\nI'll use real-time financial data to provide you with comprehensive investment analysis!"
        }}
      /> */}
    </main>
  );
}

function YourMainContent({ themeColor }: { themeColor: string }) {
  //🪁 Generative UI: https://docs.copilotkit.ai/coagents/generative-ui
  useCopilotAction({
    name: "*",
    render: (props: CatchAllActionRenderProps) => <Tool {...props} themeColor={themeColor} />,
  });

  return (
    <div
      style={{ backgroundColor: themeColor }}
      className="h-screen w-screen flex justify-center items-center flex-col transition-colors duration-300"
    >
      {
        /*
         *  TODO: Make this configurable using NEXT_PUBLIC_GRADIO_URL env var,
         *  to be accessible during build time for string substitution
         */
      }
      <iframe src="http://localhost:7860" style={{width: "100vw", height: "100vh"}} />
    </div>
  );
}
