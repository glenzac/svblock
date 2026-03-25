interface axi_if;
    logic valid;
    logic ready;
    modport master (output valid, input ready);
    modport slave  (input valid, output ready);
endinterface

module iface_mod (
    input  logic      clk,
    axi_if.master     axi_m,
    axi_if.slave      axi_s
);
endmodule
