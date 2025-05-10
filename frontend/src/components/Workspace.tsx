import React from 'react';
import SideChatBot from './Sidebar';

const Workspace = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="w-screen h-screen flex">
            {/* Sidebar */}
            <div className="w-[430px] min-w-[320px] h-full">
               <SideChatBot />
            </div>

            {/* Main Compose Panel */}
            <div className="flex-1">
                <div className="bg-white rounded-lg h-full p-4 shadow-md">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Workspace;
