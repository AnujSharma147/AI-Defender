import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { BrowserRouter, Routes, Route } from "react-router-dom";

import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

import "./App.css";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>

      <TooltipProvider>

        {/* Notifications */}
        <Toaster />
        <Sonner />

        {/* Router */}
        <BrowserRouter>

          <Routes>

            {/* Main page */}
            <Route path="/" element={<Index />} />

            {/* Catch all */}
            <Route path="*" element={<NotFound />} />

          </Routes>

        </BrowserRouter>

      </TooltipProvider>

    </QueryClientProvider>
  );
}