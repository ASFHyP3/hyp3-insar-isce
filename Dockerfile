FROM continuumio/miniconda3:4.7.12

ARG CONDA_GID=1000
ARG CONDA_UID=1000

RUN groupadd -g "${CONDA_GID}" --system conda && \
    useradd -l -u "${CONDA_UID}" -g "${CONDA_GID}" --system -d /home/conda -m  -s /bin/bash conda && \
    chown -R conda:conda /opt && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/conda/.profile && \
    echo "conda activate base" >> /home/conda/.profile

USER ${CONDA_UID}
SHELL ["/bin/bash", "-l", "-c"]
ENV PYTHONDONTWRITEBYTECODE=true
WORKDIR /home/conda/

RUN conda create -y -c conda-forge -n hyp3-inar-isce python=3.8 \
    boto3 gdal imageio lxml netCDF4 matplotlib numpy pillow \
    proj4 psycopg2 scipy six statsmodels && \
    conda clean -afy && \
    conda activate hyp3-inar-isce && \
    sed -i 's/conda activate base/conda activate hyp3-inar-isce/g' /home/conda/.profile

ARG S3_PYPI_HOST

RUN python -m pip install --no-cache-dir hyp3insarisce \
    --trusted-host "${S3_PYPI_HOST}" \
    --extra-index-url "http://${S3_PYPI_HOST}"

ENTRYPOINT ["conda", "run", "-n", "hyp3-inar-isce", "proc_insar_isce.py"]
CMD ["-v"]
