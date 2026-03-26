module heuristic (
    input  logic       clk,
    input  logic       sys_clock,
    input  logic       rst_n,
    input  logic       reset_sync,
    input  logic [7:0] data_in,
    input  logic       valid,
    output logic [7:0] data_out,
    output logic       ready,
    inout  logic       bidir
);
endmodule
