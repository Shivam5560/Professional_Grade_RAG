import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthPanel } from "@/components/auth/AuthPanel";

describe("AuthPanel", () => {
  it("submits login credentials", async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<AuthPanel onLogin={onLogin} onRegister={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(/email/i), "shivam@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret-pass");
    await userEvent.click(screen.getByRole("button", { name: /enter nexusmind/i }));
    expect(onLogin).toHaveBeenCalledWith({ email: "shivam@example.com", password: "secret-pass" });
  });

  it("blocks mismatched registration passwords", async () => {
    const onRegister = vi.fn();
    render(<AuthPanel onLogin={vi.fn()} onRegister={onRegister} />);
    await userEvent.click(screen.getByRole("tab", { name: /create account/i }));
    await userEvent.type(screen.getByLabelText(/full name/i), "Shivam Sourav");
    await userEvent.type(screen.getByLabelText(/email/i), "shivam@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret-pass");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "different-pass");
    await userEvent.click(screen.getByRole("button", { name: /create workspace/i }));
    expect(onRegister).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/passwords do not match/i);
  });
});
