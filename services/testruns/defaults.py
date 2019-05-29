

DEPLOYER_TIMEOUT = 10

# execution_metrics_metadata is populated with this default at testrun startup
# TODO: remove or adjust when frontend has a drag-n-drop interface ready for this
DEFAULT_CHART_CONFIGURATION = '''{
  "charts": [
    {
      "title": "Global Throughput",
      "type": "line",
      "node_name": "global_throughput",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "value",
      "y_format": "number",
      "y_label": "name"
    },
    {
      "title": "Global CPU usage",
      "type": "line",
      "node_name": "global_cpu",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "value",
      "y_format": "percent",
      "y_label": "name"
    },
    {
      "title": "Global Memory Usage",
      "type": "line",
      "node_name": "global_memory",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "value",
      "y_format": "bytes",
      "y_label": "name"
    },
    {
      "title": "Global Disk Usage",
      "type": "line",
      "node_name": "global_disc_data",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "value",
      "y_format": "bytes",
      "y_label": "name"
    },
    {
      "title": "Source Input per App",
      "type": "line",
      "node_name": "apps_source_input",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "source_input",
      "y_format": "number",
      "y_label": "app_name"
    },
    {
      "title": "Threads per App",
      "type": "line",
      "node_name": "apps_threads",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "threads_num",
      "y_format": "number",
      "y_label": "app_name"
    },
    {
      "title": "CPU Usage per App",
      "type": "line",
      "node_name": "apps_cpu",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "cpu",
      "y_format": "percent",
      "y_label": "app_name"
    },
    {
      "title": "WActions per App",
      "type": "line",
      "node_name": "apps_wactions",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "wactions_created",
      "y_format": "number",
      "y_label": "app_name"
    },
    {
      "title": "Latency per App",
      "type": "line",
      "node_name": "apps_latency",
      "x_data_key": "timestamp",
      "x_format": "number",
      "y_data_key": "latency",
      "y_format": "number",
      "y_label": "app_component"
    }
  ]
}'''

# chart conf for configuration with NFS extension
NFS_CHART_CONFIGURATION = '''{
  "charts": [
    {
      "x_format": "number",
      "node_name": "current_files",
      "x_data_key": "timestamp",
      "y_format": "number",
      "y_label": "name",
      "title": "Current files",
      "type": "line",
      "y_data_key": "value"
    },
    {
      "x_format": "number",
      "node_name": "current_bytes",
      "x_data_key": "timestamp",
      "y_format": "bytes",
      "y_label": "name",
      "title": "Current bytes",
      "type": "line",
      "y_data_key": "value"
    },
    {
      "x_format": "number",
      "node_name": "throughput",
      "x_data_key": "timestamp",
      "y_format": "number",
      "y_label": "name",
      "title": "Throughput",
      "type": "line",
      "y_data_key": "value"
    },
    {
      "x_format": "number",
      "node_name": "dedupe",
      "x_data_key": "timestamp",
      "y_format": "percent",
      "y_label": "name",
      "title": "Dedupe",
      "type": "line",
      "y_data_key": "value"
    },
    {
      "x_format": "number",
      "node_name": "compression",
      "x_data_key": "timestamp",
      "y_format": "number",
      "y_label": "name",
      "title": "Compression",
      "type": "line",
      "y_data_key": "value"
    },
    {
      "x_format": "number",
      "node_name": "total_savings",
      "x_data_key": "timestamp",
      "y_format": "percent",
      "y_label": "name",
      "title": "Total Savings",
      "type": "line",
      "y_data_key": "value"
    }
  ]
}'''
