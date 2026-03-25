module bus_mod #(
    parameter int WIDTH = 8
)(
    input  logic [WIDTH-1:0] data_in,
    output logic [WIDTH-1:0] data_out,
    input  logic [3:0]       nibble,
    input  logic [3:0][7:0]  matrix
);
endmodule
