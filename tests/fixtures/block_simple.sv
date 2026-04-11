// Simple hierarchy for block diagram testing.
// top instantiates mod_a, mod_b, mod_c.
// Connections: u_a -> u_c, u_b -> u_c. No connection between u_a and u_b.

module mod_a(
    input  logic        clk,
    input  logic [7:0]  data_in,
    output logic [7:0]  data_out
);
    assign data_out = data_in;
endmodule

module mod_b(
    input  logic        clk,
    input  logic [7:0]  b_in,
    output logic [7:0]  b_out
);
    assign b_out = b_in;
endmodule

module mod_c(
    input  logic        clk,
    input  logic [7:0]  c_in1,
    input  logic [7:0]  c_in2,
    output logic [7:0]  c_out
);
    assign c_out = c_in1 ^ c_in2;
endmodule

module top(
    input  logic        clk,
    input  logic [7:0]  x,
    output logic [7:0]  y
);
    logic [7:0] a_to_c, b_to_c;

    mod_a u_a(.clk(clk), .data_in(x),     .data_out(a_to_c));
    mod_b u_b(.clk(clk), .b_in(x),        .b_out(b_to_c));
    mod_c u_c(.clk(clk), .c_in1(a_to_c),  .c_in2(b_to_c), .c_out(y));
endmodule
