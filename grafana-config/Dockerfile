FROM grafana/grafana:latest
USER root
COPY grafana.ini /etc/grafana/grafana.ini
COPY provisioning/ /etc/grafana/provisioning/
RUN mkdir -p /var/lib/grafana && chown -R 472:472 /var/lib/grafana && chmod 755 /var/lib/grafana
USER 472
