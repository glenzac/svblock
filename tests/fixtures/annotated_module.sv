module annotated (
    // @sym group="Clocks"
    input  logic       clk,
    input  logic       rst_n,

    // @sym group="Data In"
    input  logic [7:0] data_in,
    input  logic       valid_in,

    // @sym group="Data Out"
    output logic [7:0] data_out,
    output logic       valid_out,

    // @sym hide=true
    output logic       debug_out
);
endmodule
