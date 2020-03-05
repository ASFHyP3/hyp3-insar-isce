FROM continuumio/miniconda3:4.7.12

# For opencontainers label definitions, see:
#    https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL org.opencontainers.image.title="HyP3 InSAR ISCE"
LABEL org.opencontainers.image.description="HyP3 plugin for InSAR processing with ISCE"
LABEL org.opencontainers.image.vendor="Alaska Satellite Facility"
LABEL org.opencontainers.image.authors="ASF APD/Tools Team <uaf-asf-apd@alaska.edu>"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.url="https://github.com/asfadmin/hyp3-insar-isce"
LABEL org.opencontainers.image.source="https://github.com/asfadmin/hyp3-insar-isce"
# LABEL org.opencontainers.image.documentation=""

# Dynamic lables to define at build time via `docker build --label`
# LABEL org.opencontainers.image.created=""
# LABEL org.opencontainers.image.version=""
# LABEL org.opencontainers.image.revision=""

# FIXME: Binutils is needed by ISCE 2.0.0 build; remove once ISCE 2.3.2+ is supported.
RUN apt-get update && apt-get install -y binutils unzip vim && apt-get clean

ARG CONDA_GID=1000
ARG CONDA_UID=1000

RUN groupadd -g "${CONDA_GID}" --system conda && \
    useradd -l -u "${CONDA_UID}" -g "${CONDA_GID}" --system -d /home/conda -m  -s /bin/bash conda && \
    conda update -n base -c defaults conda && \
    chown -R conda:conda /opt && \
    conda clean -afy && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/conda/.profile && \
    echo "conda activate base" >> /home/conda/.profile

USER ${CONDA_UID}
SHELL ["/bin/bash", "-l", "-c"]
ENV PYTHONDONTWRITEBYTECODE=true
WORKDIR /home/conda/

# FIXME: Check installs once ISCE 2.3.2+ is supported.
RUN conda create -y -c conda-forge -n hyp3-insar-isce python=3.7 \
    boto3 fftw gdal hdf5 h5py imageio imagemagick libgdal lxml netCDF4 matplotlib numpy \
    opencv=3.4 pillow proj psycopg2 requests scipy six statsmodels \
    xorg-libxt xorg-libxft xorg-libxmu xorg-libxdmcp openmotif \
    gcc_linux-64 gxx_linux-64 gfortran_linux-64 cython scons openmotif-dev && \
    conda clean -afy && \
    conda activate hyp3-insar-isce && \
    sed -i 's/conda activate base/conda activate hyp3-insar-isce/g' /home/conda/.profile

# FIXME: Remove once conda-forge ISCE 2.3.2+ is supported.
COPY --chown=conda:conda isce-2.0.0_20160906 /home/conda/isce-2.0.0_20160906
COPY --chown=conda:conda hyp3insarisce/etc/install_isce.sh /home/conda/isce-2.0.0_20160906
RUN pushd isce-2.0.0_20160906 && bash -l install_isce.sh && popd && \
    rm -r isce-2.0.0_20160906

ARG S3_PYPI_HOST

RUN python -m pip install --no-cache-dir hyp3insarisce \
    --trusted-host "${S3_PYPI_HOST}" \
    --extra-index-url "http://${S3_PYPI_HOST}"

ENTRYPOINT ["/bin/bash", "-l", "-c", "proc_insar_isce.py"]
CMD ["-v"]
