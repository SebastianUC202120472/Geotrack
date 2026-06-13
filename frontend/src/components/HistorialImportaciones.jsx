import { useEffect, useState } from "react";
import { getPedidos } from "../services/api";

export default function HistorialImportaciones() {

  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarPedidos();
  }, []);

  const cargarPedidos = async () => {
    try {
      const data = await getPedidos();
      setPedidos(data);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">

      <div className="flex justify-between items-center mb-5">

        <h2 className="text-xl font-bold">
          Últimos Pedidos Importados
        </h2>

        <button
          onClick={cargarPedidos}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Actualizar
        </button>

      </div>

      {loading ? (

        <div className="text-center py-10 text-slate-500">
          Cargando pedidos...
        </div>

      ) : (

        <table className="w-full">

          <thead>

            <tr className="border-b text-slate-500">

              <th className="text-left py-3">
                Código
              </th>

              <th className="text-left">
                Cliente
              </th>

              <th className="text-left">
                Destinatario
              </th>

              <th className="text-left">
                Distrito
              </th>

              <th className="text-left">
                Estado
              </th>

            </tr>

          </thead>

          <tbody>

            {pedidos.length === 0 ? (

              <tr>
                <td
                  colSpan="5"
                  className="text-center py-8 text-slate-400"
                >
                  No existen pedidos importados.
                </td>
              </tr>

            ) : (

              pedidos.map((pedido) => (

                <tr
                  key={pedido.id}
                  className="border-b hover:bg-slate-50"
                >

                  <td className="py-3 font-medium">
                    {pedido.codigo}
                  </td>

                  <td>
                    {pedido.cliente_origen}
                  </td>

                  <td>
                    {pedido.nombre_destinatario}
                  </td>

                  <td>
                    {pedido.distrito || "-"}
                  </td>

                  <td>

                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        pedido.estado === "PENDIENTE"
                          ? "bg-yellow-100 text-yellow-700"
                          : pedido.estado === "ENTREGADO"
                          ? "bg-green-100 text-green-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {pedido.estado}
                    </span>

                  </td>

                </tr>

              ))

            )}

          </tbody>

        </table>

      )}

    </div>
  );
}