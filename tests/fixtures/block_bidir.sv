// Bidirectional connection test: mod_a and mod_b exchange signals.

module mod_a(
    input  logic        clk,
    input  logic [7:0]  from_b,
    output logic [7:0]  to_b
);
    assign to_b = from_b;
endmodule

module mod_b(
    input  logic        clk,
    input  logic [7:0]  from_a,
    output logic [7:0]  to_a
);
    assign to_a = from_a;
endmodule

module top_bidir(
    input  logic        clk,
    input  logic [7:0]  x,
    output logic [7:0]  y
);
    logic [7:0] a2b, b2a;

    mod_a u_a(.clk(clk), .from_b(b2a), .to_b(a2b));
    mod_b u_b(.clk(clk), .from_a(a2b), .to_a(b2a));

    assign y = a2b ^ b2a;
endmodule
