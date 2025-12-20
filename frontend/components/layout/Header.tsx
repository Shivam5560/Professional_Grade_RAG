import { Brain, Bell, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/auth");
  };

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl px-6 shadow-lg shadow-cyan-500/5">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30 ring-2 ring-cyan-500/20">
          <Brain className="h-6 w-6 text-white" />
        </div>
        <span className="text-xl font-black tracking-tight bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
          NexusMind RAG
        </span>
      </div>
      
      <div className="flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="icon" 
          className="text-slate-400 hover:text-cyan-400 hover:bg-slate-800/50 transition-all"
        >
          <Bell className="h-5 w-5" />
        </Button>
        
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="icon" 
                className="rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/30"
              >
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-slate-900/95 border-slate-800/50 backdrop-blur-xl">
              <DropdownMenuLabel className="text-white">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-slate-800/50" />
              <DropdownMenuItem className="text-xs text-slate-400 focus:text-white focus:bg-slate-800/50">
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-slate-800/50" />
              <DropdownMenuItem 
                onClick={handleLogout} 
                className="text-red-400 focus:text-red-300 focus:bg-red-500/10"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button onClick={() => router.push("/auth")} className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/30">
            Login
          </Button>
        )}
      </div>
    </header>
  );
}
