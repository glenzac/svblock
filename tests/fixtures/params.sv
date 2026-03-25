module param_mod #(
    parameter int          WIDTH = 8,
    parameter type         T     = logic,
    parameter string       NAME  = "default",
    localparam int         DEPTH = 16
)(
    input  logic clk
);
endmodule
