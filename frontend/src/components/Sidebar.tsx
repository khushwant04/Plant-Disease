/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
import React, { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

const SideChatBot = () => {
    interface Message {
        from: string;
        text: string;
        loading?: boolean;
    }

    const [messages, setMessages] = useState<Message[]>([
        { from: "bot", text: "Hi! Upload an image to get started." }
    ]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTo({
                    top: scrollContainer.scrollHeight,
                    behavior: 'smooth',
                });
            }
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        // Add user message
        setMessages((prev) => [...prev, { from: "user", text: input }]);

        // Add loading message placeholder
        setMessages((prev) => [...prev, { from: "bot", text: "", loading: true }]);

        setInput("");
        setIsStreaming(true);

        try {
            const response = await fetch("http://localhost:8000/generate-stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ input }),
            });

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder("utf-8");

            if (!reader) {
                throw new Error("Failed to initialize stream reader");
            }

            // Replace loading placeholder with empty message that will be streamed into
            setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = { from: "bot", text: "" };
                return updated;
            });

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);

                setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last.from === "bot") {
                        updated[updated.length - 1] = {
                            ...last,
                            text: last.text + chunk,
                            loading: false
                        };
                    } else {
                        updated.push({ from: "bot", text: chunk, loading: false });
                    }
                    return updated;
                });
            }
        } catch (error) {
            console.error("Error during streaming:", error);
            setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.loading) {
                    updated[updated.length - 1] = {
                        from: "bot",
                        text: `Error: ${error instanceof Error ? error.message : "Failed to connect to server"}`,
                        loading: false
                    };
                } else {
                    updated.push({
                        from: "bot",
                        text: `Error: ${error instanceof Error ? error.message : "Failed to connect to server"}`,
                        loading: false
                    });
                }
                return updated;
            });
        } finally {
            setIsStreaming(false);
        }
    };

    // Custom components for the ReactMarkdown
    const MarkdownComponents = {
        // Style the headings
        h1: (props: any) => <h1 className="text-2xl font-bold my-4" {...props} />,
        h2: (props: any) => <h2 className="text-xl font-bold my-3" {...props} />,
        h3: (props: any) => <h3 className="text-lg font-bold my-2" {...props} />,
        // Style the lists
        ul: (props: any) => <ul className="list-disc ml-6 my-2" {...props} />,
        ol: (props: any) => <ol className="list-decimal ml-6 my-2" {...props} />,
        // Style the code blocks
        code: (props: any) => {
            const { children, className } = props;
            const match = /language-(\w+)/.exec(className || '');
            return match ? (
                <div className="rounded bg-gray-800 p-2 my-2 overflow-x-auto">
                    <pre className="text-sm text-white">
                        <code className={className}>{children}</code>
                    </pre>
                </div>
            ) : (
                <code className="bg-gray-100 px-1 rounded text-sm">{children}</code>
            );
        },
        // Style the blockquotes
         
        blockquote: (props: any) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props} />
        ),
        // Style links
         
        a: (props: any) => <a className="text-blue-500 hover:underline" {...props} />,
        // Style paragraphs
        p: (props: any) => <p className="my-2" {...props} />,
    };

    return (
        <div className="w-[400px] h-screen text-gray-900 bg-white flex flex-col">
            <div className="p-4 text-lg font-semibold border-b">
                🌿 PlantAI Assistant
            </div>
            <ScrollArea ref={scrollAreaRef} className="flex-1 p-2 space-y-2 overflow-auto bg-white">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`p-3 m-2 rounded-xl max-w-[90%] ${msg.from === "bot"
                                ? "bg-gray-100 text-left ml-0 mr-auto"
                                : "bg-gray-200 text-black text-left ml-auto mr-0"
                            }`}
                    >
                        {msg.loading ? (
                            <div className="flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Thinking...</span>
                            </div>
                        ) : msg.from === "bot" ? (
                            <div className="markdown-content">
                                <ReactMarkdown
                                    components={MarkdownComponents}
                                    remarkPlugins={[remarkGfm]}
                                    rehypePlugins={[rehypeRaw, rehypeSanitize]}
                                >
                                    {msg.text}
                                </ReactMarkdown>
                            </div>
                        ) : (
                            <div className="whitespace-pre-wrap">{msg.text}</div>
                        )}
                    </div>
                ))}
            </ScrollArea>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                }}
                className="p-4 border-t border-gray-300 flex gap-2"
            >
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 bg-white text-gray-900"
                    placeholder="Ask about the diagnosis..."
                    disabled={isStreaming}
                />
                <Button type="submit" disabled={isStreaming}>
                    {isStreaming ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : "Send"}
                </Button>
            </form>
        </div>
    );
};

export default SideChatBot;
