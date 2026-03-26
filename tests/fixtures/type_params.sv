module type_params #(
    parameter type          T       = logic,
    parameter int           WIDTH   = 8,
    parameter string        NAME    = "default",
    localparam int          DEPTH   = 32
)(
    input  T                data_in,
    output logic [WIDTH-1:0] data_out
);
endmodule
