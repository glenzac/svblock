// Single-instance degenerate case.

module inner(
    input  logic [7:0] d_in,
    output logic [7:0] d_out
);
    assign d_out = d_in;
endmodule

module wrapper(
    input  logic [7:0] x,
    output logic [7:0] y
);
    inner u0(.d_in(x), .d_out(y));
endmodule
