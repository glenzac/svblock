module large_mod #(
    parameter int DATA_W  = 32,
    parameter int ADDR_W  = 16,
    parameter int ID_W    = 4
)(
    // @sym group="Clocks & Resets"
    input  logic              clk,
    input  logic              rst_n,

    // @sym group="Write Channel"
    input  logic [ADDR_W-1:0] wr_addr,
    input  logic [DATA_W-1:0] wr_data,
    input  logic [3:0]        wr_strb,
    input  logic              wr_valid,
    output logic              wr_ready,
    input  logic [ID_W-1:0]   wr_id,

    // @sym group="Read Channel"
    input  logic [ADDR_W-1:0] rd_addr,
    input  logic              rd_valid,
    output logic              rd_ready,
    output logic [DATA_W-1:0] rd_data,
    output logic              rd_resp,
    output logic [ID_W-1:0]   rd_id,

    // @sym group="Control"
    input  logic              enable,
    input  logic [1:0]        mode,
    output logic              busy,
    output logic              error,

    // @sym group="Status"
    output logic [7:0]        fifo_count,
    output logic              fifo_full,
    output logic              fifo_empty,

    // @sym group="Interrupts"
    output logic              irq,
    output logic              irq_wr_done,
    output logic              irq_rd_done,
    output logic              irq_error
);
endmodule
